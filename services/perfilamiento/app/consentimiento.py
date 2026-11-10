"""Validacion de consentimiento Open Finance en Perfilamiento (EXP-007, HU3.2.1).

Tacticas:
  - Autenticar actores: el llamador de GET /perfiles trae un JWT con scope perfil:read.
  - Autorizar actores (fail-closed): antes de entregar datos financieros se verifica
    que el cliente tenga consentimiento vigente en Consentimiento Open Finance. Si
    no se puede verificar (timeout, error, 5xx), se NIEGA el acceso.
  - Revocar acceso: la respuesta de Consentimiento se guarda en una cache local con
    TTL (CONSENT_CACHE_TTL_S, 60 s). Al expirar, Perfilamiento vuelve a preguntar, asi
    que una revocacion se nota a mas tardar en TTL segundos.
  - Pista de auditoria: cada acceso negado se reporta a Consentimiento (audit_log)
    en un hilo aparte, para no sumar latencia a la respuesta.

Todo esto solo corre con CONSENT_CHECK_ENABLED=true. Apagado, GET /perfiles se
comporta como la base compartida (sin token y sin verificar consentimiento).

Uso en main.py (la dependencia corre ANTES del cuerpo del endpoint, es decir antes
de cualquier llamada a Open Finance y antes de cualquier cache de perfiles):

    from .consentimiento import verificar_acceso
    @app.get("/perfiles/{cliente_id}", dependencies=[Depends(verificar_acceso)])
"""
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import uuid
from dataclasses import dataclass

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

log = logging.getLogger("perfilamiento.consentimiento")

CONSENT_CHECK_ENABLED = os.getenv("CONSENT_CHECK_ENABLED", "false").lower() == "true"
CONSENTIMIENTO_URL = os.getenv("CONSENTIMIENTO_URL", "http://localhost:8000").rstrip("/")
CONSENT_CACHE_TTL_S = float(os.getenv("CONSENT_CACHE_TTL_S", "60"))
CONSENT_TIMEOUT_S = float(os.getenv("CONSENT_TIMEOUT_S", "1.0"))
FUENTE = "open_finance"

# TLS hacia Consentimiento (HTTPS en el ALB con certificado autofirmado):
#   "true"  -> valida contra las CA del sistema
#   "false" -> no valida (solo pruebas)
#   ruta    -> valida contra ese certificado (recomendado con el autofirmado)
_tls = os.getenv("CONSENTIMIENTO_TLS_VERIFY", "true")
TLS_VERIFY: bool | str = {"true": True, "false": False}.get(_tls.lower(), _tls)

JWT_SECRET = os.getenv("JWT_SECRET", "cambiar-en-despliegue")
JWT_ALGORITMO = "HS256"
SERVICIO = os.getenv("SERVICE_NAME", "perfilamiento")

ROLES_LECTORES = {"servicio", "analista"}  # RBAC de GET /perfiles (ademas del propio cliente)

_bearer = HTTPBearer(auto_error=False)


# ---------- Cache local con TTL (cache-aside) ----------


@dataclass
class _Entrada:
    vigente: bool
    expira: float  # time.monotonic()


class CacheConsentimiento:
    def __init__(self, ttl_s: float):
        self.ttl_s = ttl_s
        self._datos: dict[uuid.UUID, _Entrada] = {}
        self._lock = threading.Lock()
        self.aciertos = 0
        self.fallos = 0

    def obtener(self, cliente_id: uuid.UUID) -> bool | None:
        with self._lock:
            e = self._datos.get(cliente_id)
            if e is None or e.expira <= time.monotonic():
                self._datos.pop(cliente_id, None)
                self.fallos += 1
                return None
            self.aciertos += 1
            return e.vigente

    def guardar(self, cliente_id: uuid.UUID, vigente: bool) -> None:
        with self._lock:
            self._datos[cliente_id] = _Entrada(vigente, time.monotonic() + self.ttl_s)


cache = CacheConsentimiento(CONSENT_CACHE_TTL_S)


# ---------- Cliente hacia Consentimiento ----------


class ConsentimientoNoVerificable(Exception):
    pass


_http = httpx.Client(timeout=CONSENT_TIMEOUT_S, verify=TLS_VERIFY)
# Pool aparte para reportar accesos negados sin bloquear la respuesta.
_auditoria = ThreadPoolExecutor(max_workers=2, thread_name_prefix="auditoria")
_token_servicio: tuple[str, float] | None = None


def _token_propio() -> str:
    """JWT de servicio de Perfilamiento (en produccion: client credentials de Cognito)."""
    global _token_servicio
    if _token_servicio is None or _token_servicio[1] - time.time() < 60:
        exp = time.time() + 3600
        token = jwt.encode(
            {"sub": SERVICIO, "rol": "servicio", "scope": "consentimiento:read auditoria:write", "exp": int(exp)},
            JWT_SECRET,
            algorithm=JWT_ALGORITMO,
        )
        _token_servicio = (token, exp)
    return _token_servicio[0]


def consultar_vigente_remoto(cliente_id: uuid.UUID) -> bool:
    try:
        r = _http.get(
            f"{CONSENTIMIENTO_URL}/consentimientos/vigente",
            params={"clienteId": str(cliente_id), "fuente": FUENTE},
            headers={"Authorization": f"Bearer {_token_propio()}"},
        )
    except httpx.HTTPError as e:
        raise ConsentimientoNoVerificable(f"error de red: {e.__class__.__name__}") from e
    if r.status_code != 200:
        raise ConsentimientoNoVerificable(f"Consentimiento respondio {r.status_code}")
    return bool(r.json().get("vigente"))


def consentimiento_vigente(cliente_id: uuid.UUID) -> bool:
    en_cache = cache.obtener(cliente_id)
    if en_cache is not None:
        return en_cache
    vigente = consultar_vigente_remoto(cliente_id)  # puede lanzar ConsentimientoNoVerificable
    cache.guardar(cliente_id, vigente)  # se guarda el si y el no; los errores NO se guardan
    return vigente


def _reportar_acceso_negado(cliente_id: uuid.UUID, motivo: str) -> None:
    try:
        _http.post(
            f"{CONSENTIMIENTO_URL}/auditoria/accesos-negados",
            json={"clienteId": str(cliente_id), "motivo": motivo},
            headers={"Authorization": f"Bearer {_token_propio()}"},
        )
    except httpx.HTTPError as e:  # si Consentimiento esta caido, queda al menos en CloudWatch
        log.warning("no se pudo registrar acceso negado cliente=%s: %s", cliente_id, e)


# ---------- Dependencia de FastAPI ----------


def _autenticar(credenciales: HTTPAuthorizationCredentials | None, cliente_id: uuid.UUID) -> str:
    if credenciales is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token Bearer")
    try:
        claims = jwt.decode(
            credenciales.credentials, JWT_SECRET, algorithms=[JWT_ALGORITMO], options={"require": ["exp", "sub"]}
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token invalido: {e}") from e
    sub, rol = str(claims["sub"]), str(claims.get("rol", ""))
    scopes = set(str(claims.get("scope", "")).split())
    es_titular = rol == "cliente" and sub == str(cliente_id)
    if "perfil:read" not in scopes or not (rol in ROLES_LECTORES or es_titular):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere scope perfil:read y rol autorizado")
    return sub


def verificar_acceso(
    cliente_id: uuid.UUID,
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    if not CONSENT_CHECK_ENABLED:
        return
    actor = _autenticar(credenciales, cliente_id)
    try:
        vigente = consentimiento_vigente(cliente_id)
    except ConsentimientoNoVerificable as e:
        motivo = f"no verificable ({e})"
        vigente = False
    else:
        motivo = "sin consentimiento vigente"
    if not vigente:
        log.info("evento=ACCESO_NEGADO cliente=%s actor=%s motivo=%s", cliente_id, actor, motivo)
        _auditoria.submit(_reportar_acceso_negado, cliente_id, motivo)
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Acceso negado: {motivo}")
