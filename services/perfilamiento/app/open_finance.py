"""Cliente de Open Finance en Perfilamiento (EXP-009, HU10.1.3).

Modulo propio de EXP-009: toda la logica de la llamada a Open Finance vive aqui,
para que main.py solo la invoque y no choque con consentimiento.py (EXP-007).

Tres configuraciones, segun dos flags (ambos apagados por defecto):

  OPEN_FINANCE_ENABLED=false
      GET /perfiles devuelve solo lo guardado en la BD (base compartida).

  OPEN_FINANCE_ENABLED=true, CIRCUIT_BREAKER_ENABLED=false     -> LINEA BASE A
      Consulta Open Finance en cada peticion con un timeout de 120 ms, sin mas
      proteccion: si el proveedor falla o tarda, la peticion falla con 502.

  OPEN_FINANCE_ENABLED=true, CIRCUIT_BREAKER_ENABLED=true      -> CONFIGURACION B
      Ademas del timeout:
        - circuit breaker: abre con >= 50 % de fallos en las ultimas 10 llamadas,
          queda abierto 30 s y luego deja pasar 3 llamadas de prueba (semiabierto);
        - bulkhead: maximo 10 llamadas simultaneas a Open Finance (pool exclusivo);
        - degradacion elegante: si Open Finance no responde, se sirve el ultimo
          perfil guardado en Redis (antiguedad maxima 24 h) y, si no hay, un
          perfil por defecto conservador. La peticion NO falla.

Redis y su libreria solo se usan con CIRCUIT_BREAKER_ENABLED=true: con el flag
apagado el servicio arranca y funciona sin Redis. Aunque el flag este encendido,
una caida de Redis no tumba el servicio (se trata como "no hay cache").

Endpoints propios (router incluido en main.py):
  GET  /ready                          readiness: solo verifica Redis, nunca Open Finance
  GET  /admin/open-finance/estado      circuito, transiciones con hora y contadores
  POST /admin/open-finance/reset       limpia contadores y transiciones
(los /admin solo responden con OPEN_FINANCE_ADMIN_ENABLED=true)
"""
import json
import logging
import os
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Response

# ---------- configuracion ----------

OPEN_FINANCE_ENABLED = os.getenv("OPEN_FINANCE_ENABLED", "false").lower() == "true"
CIRCUIT_BREAKER_ENABLED = os.getenv("CIRCUIT_BREAKER_ENABLED", "false").lower() == "true"
OPEN_FINANCE_URL = os.getenv("OPEN_FINANCE_URL", "http://localhost:18009").rstrip("/")
OPEN_FINANCE_TIMEOUT_S = float(os.getenv("OPEN_FINANCE_TIMEOUT_S", "0.12"))  # presupuesto por dependencia (caso §6.1)

CB_VENTANA = int(os.getenv("CB_VENTANA", "10"))  # llamadas que se miran
CB_TASA_FALLOS = float(os.getenv("CB_TASA_FALLOS", "0.5"))  # 50 %
CB_ABIERTO_S = float(os.getenv("CB_ABIERTO_S", "30"))
CB_PRUEBAS = int(os.getenv("CB_PRUEBAS", "3"))  # llamadas de prueba en semiabierto
BULKHEAD_MAX = int(os.getenv("BULKHEAD_MAX", "10"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
PERFIL_CACHE_MAX_EDAD_S = int(os.getenv("PERFIL_CACHE_MAX_EDAD_S", str(24 * 3600)))
ADMIN_ENABLED = os.getenv("OPEN_FINANCE_ADMIN_ENABLED", "false").lower() == "true"

# Perfil por defecto conservador: supuestos de mayor riesgo cuando no hay datos.
PERFIL_POR_DEFECTO = {
    "ingresoMensual": None,
    "endeudamiento": 0.5,
    "mora30d": 2,
    "antiguedadMeses": 0,
    "origen": "perfil-por-defecto",
}

# Logger propio (no altera la configuracion de logging del resto del servicio).
log = logging.getLogger("perfilamiento.open_finance")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
    log.propagate = False


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ---------- metricas ----------


class Metricas:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reiniciar()

    def reiniciar(self) -> None:
        with self._lock:
            self.contadores = {
                "total": 0,
                "openFinanceOk": 0,
                "openFinanceFallo": 0,
                "servidasDesdeCache": 0,
                "servidasPerfilPorDefecto": 0,
                "rechazadasCircuitoAbierto": 0,
                "rechazadasBulkheadLleno": 0,
                "fallosRedis": 0,
            }
            self.transiciones: deque = deque(maxlen=100)

    def sumar(self, nombre: str) -> None:
        with self._lock:
            self.contadores[nombre] += 1

    def transicion(self, estado: str, motivo: str) -> None:
        with self._lock:
            self.transiciones.append({"estado": estado, "desde": _ahora_iso(), "motivo": motivo})

    def foto(self) -> dict:
        with self._lock:
            return {"contadores": dict(self.contadores), "transiciones": list(self.transiciones)}


metricas = Metricas()


# ---------- circuit breaker (estado por proceso) ----------

CERRADO, ABIERTO, SEMIABIERTO = "CERRADO", "ABIERTO", "SEMIABIERTO"


class CircuitBreaker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.estado = CERRADO
        self._ventana: deque = deque(maxlen=CB_VENTANA)
        self._abierto_desde = 0.0
        self._pruebas_lanzadas = 0
        self._pruebas_ok = 0

    def _cambiar(self, estado: str, motivo: str) -> None:
        self.estado = estado
        log.info("evento=CIRCUITO estado=%s motivo=%s", estado, motivo)
        metricas.transicion(estado, motivo)

    def _abrir(self, motivo: str) -> None:
        self._abierto_desde = time.monotonic()
        self._cambiar(ABIERTO, motivo)

    def permitir(self) -> str | None:
        """Devuelve el permiso con el que se hace la llamada, o None si no se debe llamar."""
        with self._lock:
            if self.estado == CERRADO:
                return CERRADO
            if self.estado == ABIERTO:
                if time.monotonic() - self._abierto_desde < CB_ABIERTO_S:
                    return None
                self._pruebas_lanzadas = 0
                self._pruebas_ok = 0
                self._cambiar(SEMIABIERTO, f"pasaron {CB_ABIERTO_S:g} s")
            if self._pruebas_lanzadas < CB_PRUEBAS:  # semiabierto: solo unas pocas llamadas de prueba
                self._pruebas_lanzadas += 1
                return SEMIABIERTO
            return None

    def registrar(self, ok: bool, permiso: str) -> None:
        with self._lock:
            if permiso == SEMIABIERTO:
                if self.estado != SEMIABIERTO:
                    return
                if not ok:
                    self._abrir("fallo una llamada de prueba")
                else:
                    self._pruebas_ok += 1
                    if self._pruebas_ok >= CB_PRUEBAS:
                        self._ventana.clear()
                        self._cambiar(CERRADO, f"{CB_PRUEBAS} llamadas de prueba correctas")
                return
            if self.estado != CERRADO:  # resultado tardio de una llamada anterior a la apertura
                return
            self._ventana.append(ok)
            if len(self._ventana) == CB_VENTANA:
                fallos = sum(1 for r in self._ventana if not r)
                if fallos / CB_VENTANA >= CB_TASA_FALLOS:
                    self._abrir(f"{fallos} fallos en las ultimas {CB_VENTANA} llamadas")


breaker = CircuitBreaker()
_bulkhead = threading.BoundedSemaphore(BULKHEAD_MAX)


# ---------- cache de perfiles en Redis (solo con CIRCUIT_BREAKER_ENABLED) ----------

_redis = None
_redis_ignorar_hasta = 0.0


def _cliente_redis(forzar: bool = False):
    """Cliente de Redis, creado la primera vez que se necesita. None si no se debe usar."""
    global _redis
    if not CIRCUIT_BREAKER_ENABLED or (not forzar and time.monotonic() < _redis_ignorar_hasta):
        return None
    if _redis is None:
        import redis  # import perezoso: sin el flag la libreria ni se carga

        _redis = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=0.05, socket_timeout=0.05)
    return _redis


def _redis_fallo(e: Exception) -> None:
    """Si Redis falla se deja de intentar 30 s, para no sumar espera a cada peticion."""
    global _redis_ignorar_hasta
    _redis_ignorar_hasta = time.monotonic() + 30
    metricas.sumar("fallosRedis")
    log.warning("evento=REDIS_NO_DISPONIBLE error=%s", e.__class__.__name__)


def _clave(cliente_id: uuid.UUID) -> str:
    return f"perfil:open-finance:{cliente_id}"


def cache_guardar(cliente_id: uuid.UUID, senales: dict) -> None:
    try:
        r = _cliente_redis()
        if r is not None:
            r.setex(_clave(cliente_id), PERFIL_CACHE_MAX_EDAD_S, json.dumps({"senales": senales, "guardadoEn": time.time()}))
    except Exception as e:  # Redis caido: no es motivo para fallar la peticion
        _redis_fallo(e)


def cache_leer(cliente_id: uuid.UUID) -> dict | None:
    try:
        r = _cliente_redis()
        if r is None:
            return None
        crudo = r.get(_clave(cliente_id))
        if crudo is None:
            return None
        dato = json.loads(crudo)
        if time.time() - float(dato["guardadoEn"]) > PERFIL_CACHE_MAX_EDAD_S:
            return None
        return dato["senales"]
    except Exception as e:
        _redis_fallo(e)
        return None


# ---------- llamada a Open Finance ----------


class OpenFinanceError(Exception):
    """Open Finance no respondio bien (error, timeout o respuesta invalida)."""


# Con el flag del breaker, el pool HTTP queda limitado (bulkhead); sin el, el pool es el de defecto.
_limites = httpx.Limits(max_connections=BULKHEAD_MAX, max_keepalive_connections=BULKHEAD_MAX) if CIRCUIT_BREAKER_ENABLED else httpx.Limits()
_http = httpx.Client(timeout=OPEN_FINANCE_TIMEOUT_S, limits=_limites)


def _consultar(cliente_id: uuid.UUID) -> dict:
    try:
        r = _http.get(f"{OPEN_FINANCE_URL}/senales/{cliente_id}")
    except httpx.HTTPError as e:
        raise OpenFinanceError(f"error de red: {e.__class__.__name__}") from e
    if r.status_code != 200:
        raise OpenFinanceError(f"Open Finance respondio {r.status_code}")
    return r.json().get("senales") or {}


def _degradar(cliente_id: uuid.UUID, motivo: str) -> dict:
    """Degradacion elegante: ultimo perfil en Redis o, si no hay, perfil por defecto."""
    en_cache = cache_leer(cliente_id)
    if en_cache is not None:
        metricas.sumar("servidasDesdeCache")
        log.info("evento=DEGRADADO origen=cache motivo=%s cliente=%s", motivo, cliente_id)
        return {**en_cache, "origen": "cache"}
    metricas.sumar("servidasPerfilPorDefecto")
    log.info("evento=DEGRADADO origen=perfil-por-defecto motivo=%s cliente=%s", motivo, cliente_id)
    return dict(PERFIL_POR_DEFECTO)


def _con_tacticas(cliente_id: uuid.UUID) -> dict:
    permiso = breaker.permitir()
    if permiso is None:
        metricas.sumar("rechazadasCircuitoAbierto")
        return _degradar(cliente_id, "circuito-abierto")
    if not _bulkhead.acquire(blocking=False):  # ya hay BULKHEAD_MAX llamadas en curso
        metricas.sumar("rechazadasBulkheadLleno")
        if permiso == SEMIABIERTO:  # no se uso la llamada de prueba: se devuelve el cupo
            with breaker._lock:
                breaker._pruebas_lanzadas = max(0, breaker._pruebas_lanzadas - 1)
        return _degradar(cliente_id, "bulkhead-lleno")
    try:
        senales = _consultar(cliente_id)
    except OpenFinanceError as e:
        breaker.registrar(False, permiso)
        metricas.sumar("openFinanceFallo")
        return _degradar(cliente_id, f"fallo-open-finance ({e})")
    finally:
        _bulkhead.release()
    breaker.registrar(True, permiso)
    metricas.sumar("openFinanceOk")
    cache_guardar(cliente_id, senales)
    return senales


def senales_open_finance(cliente_id: uuid.UUID, guardadas: dict | None) -> dict | None:
    """Señales de Open Finance para el perfil del cliente (ver el docstring del modulo)."""
    if not OPEN_FINANCE_ENABLED:
        return guardadas
    metricas.sumar("total")
    if CIRCUIT_BREAKER_ENABLED:
        return _con_tacticas(cliente_id)
    try:  # linea base A: solo timeout
        senales = _consultar(cliente_id)
    except OpenFinanceError as e:
        metricas.sumar("openFinanceFallo")
        log.warning("open_finance fallo cliente=%s: %s", cliente_id, e)
        raise HTTPException(status_code=502, detail=f"Open Finance no disponible: {e}") from e
    metricas.sumar("openFinanceOk")
    return senales


# ---------- endpoints propios ----------

router = APIRouter()


@router.get("/ready")
def ready(response: Response):
    """Readiness: verifica SOLO Redis (y solo si el breaker esta activo).

    Open Finance no entra aqui a proposito: si su caida marcara las tareas como
    no saludables, el balanceador las retiraria y se perderia la degradacion.
    """
    if not CIRCUIT_BREAKER_ENABLED:
        return {"status": "ready", "redis": "no-requerido"}
    try:
        _cliente_redis(forzar=True).ping()  # readiness comprueba Redis de verdad, sin la pausa de reintentos
        return {"status": "ready", "redis": "ok"}
    except Exception as e:
        response.status_code = 503
        return {"status": "not-ready", "redis": f"error: {e.__class__.__name__}"}


def _exigir_admin() -> None:
    if not ADMIN_ENABLED:
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/admin/open-finance/estado")
def estado_open_finance():
    _exigir_admin()
    foto = metricas.foto()
    return {
        "openFinanceEnabled": OPEN_FINANCE_ENABLED,
        "circuitBreakerEnabled": CIRCUIT_BREAKER_ENABLED,
        "circuito": breaker.estado,
        "timeoutS": OPEN_FINANCE_TIMEOUT_S,
        "bulkheadMax": BULKHEAD_MAX,
        **foto,
    }


@router.post("/admin/open-finance/reset")
def reset_open_finance():
    _exigir_admin()
    metricas.reiniciar()
    return {"ok": True}
