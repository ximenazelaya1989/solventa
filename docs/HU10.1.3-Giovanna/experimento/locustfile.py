"""EXP-009: prueba de carga con Locust (10 TPS constantes, 3 fases).

  Fase 1 (normal)      0-5 min:  Open Finance sano; solo se consultan los clientes 0..799
  Fase 2 (falla)       5-15 min: el script tumba el mock; se consultan los 1.000 clientes
  Fase 3 (recuperacion) 15-20 min: el script restaura el mock

La carga es siempre POST /v1/cotizaciones (por el gateway) a 10 TPS: 10 usuarios,
cada uno con exactamente 1 peticion por segundo.

Variables de entorno (todas opcionales):
  FASE1_S=300 FASE2_S=600 FASE3_S=300   duracion de cada fase en segundos
  TPS=10                                 peticiones por segundo
  MODO_FALLA=error503                    error503 | lento2s
  MOCK_URL=http://localhost:18009        mock de Open Finance
  PERF_ADMIN_URLS=http://localhost:18002 URLs de cada tarea de Perfilamiento (separadas por coma)
  SALIDA=resultados/B1                   carpeta de salida (requests.csv, estado_final.json)

Ejecucion:
  locust -f locustfile.py --headless --host http://localhost:18080 -u 10 -r 10
(la forma de la carga termina la prueba sola; no hace falta --run-time)
"""
import csv
import json
import os
import random
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

import gevent
from locust import HttpUser, LoadTestShape, events, task

NS = uuid.UUID("a1b2c3d4-0000-4000-8000-000000000009")  # mismo valor que preparar_datos.py
PRODUCTO = "22222222-2222-2222-2222-222222222222"
N_TOTAL, N_CON_CACHE = 1000, 800

F1 = int(os.getenv("FASE1_S", "300"))
F2 = int(os.getenv("FASE2_S", "600"))
F3 = int(os.getenv("FASE3_S", "300"))
TPS = int(os.getenv("TPS", "10"))
MODO_FALLA = os.getenv("MODO_FALLA", "error503")
MOCK_URL = os.getenv("MOCK_URL", "http://localhost:18009").rstrip("/")
PERF_ADMIN_URLS = [u.strip().rstrip("/") for u in os.getenv("PERF_ADMIN_URLS", "http://localhost:18002").split(",") if u.strip()]
SALIDA = Path(os.getenv("SALIDA", "resultados/corrida"))

filas: list[dict] = []
marcas: dict = {}


def cliente(i: int) -> str:
    return str(uuid.uuid5(NS, f"cliente-{i}"))


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds")


def http(url: str, metodo: str = "GET", cuerpo=None):
    data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    r = urllib.request.Request(url, data=data, method=metodo, headers={"content-type": "application/json"})
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read() or b"null")


def fase_de(t_rel: float) -> int:
    return 1 if t_rel < F1 else 2 if t_rel < F1 + F2 else 3


def inyectar_falla() -> None:
    """Corre en segundo plano: tumba el mock al terminar la fase 1 y lo restaura al terminar la 2."""
    gevent.sleep(F1)
    http(f"{MOCK_URL}/admin/fail", "POST", {"modo": MODO_FALLA})
    marcas["falla_ts"] = time.time()
    print(f"[{iso(marcas['falla_ts'])}] FALLA inyectada: modo={MODO_FALLA}")
    gevent.sleep(F2)
    http(f"{MOCK_URL}/admin/fail", "POST", {"modo": "ok"})
    marcas["restauracion_ts"] = time.time()
    print(f"[{iso(marcas['restauracion_ts'])}] Open Finance RESTAURADO")


def calentar(host: str) -> None:
    """Calentamiento previo (NO se mide): abre las conexiones entre servicios.

    Sin esto, las primeras peticiones simultaneas del arranque pagan el costo de
    abrir conexiones nuevas y pueden superar los 120 ms del timeout, lo que no
    tiene que ver con las tacticas ni con la falla de Open Finance.
    """
    def tanda(k: int) -> None:
        for j in range(3):
            try:
                http(f"{host}/v1/cotizaciones", "POST", {"clienteId": cliente((k * 3 + j) % N_CON_CACHE), "productoId": PRODUCTO})
            except Exception:
                pass

    gevent.joinall([gevent.spawn(tanda, k) for k in range(TPS)], timeout=30)


@events.test_start.add_listener
def al_empezar(environment, **kw):
    http(f"{MOCK_URL}/admin/fail", "POST", {"modo": "ok"})
    if os.getenv("CALENTAR", "1") == "1" and environment.host:
        calentar(environment.host.rstrip("/"))
    http(f"{MOCK_URL}/admin/reset", "POST")
    for u in PERF_ADMIN_URLS:
        http(f"{u}/admin/open-finance/reset", "POST")
    filas.clear()
    marcas.clear()
    marcas["inicio_ts"] = time.time()
    gevent.spawn(inyectar_falla)


@events.test_stop.add_listener
def al_terminar(environment, **kw):
    SALIDA.mkdir(parents=True, exist_ok=True)
    with open(SALIDA / "requests.csv", "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "t_rel_s", "fase", "clienteIdx", "status", "ok", "latencia_ms"])
        w.writeheader()
        w.writerows(filas)
    estado = {
        "config": {"F1": F1, "F2": F2, "F3": F3, "TPS": TPS, "modoFalla": MODO_FALLA},
        "marcas": {k: iso(v) for k, v in marcas.items()},
        "mock": http(f"{MOCK_URL}/admin/estado"),
        "perfilamiento": {u: http(f"{u}/admin/open-finance/estado") for u in PERF_ADMIN_URLS},
    }
    (SALIDA / "estado_final.json").write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf8")
    print(f"Resultados en {SALIDA}/ ({len(filas)} peticiones)")


class Cotizador(HttpUser):
    # Cada usuario hace exactamente 1 peticion por segundo; con TPS usuarios hay TPS peticiones/s.
    # Los usuarios entran escalonados en el primer segundo y conservan su desfase, asi las
    # peticiones llegan repartidas (no en rafagas de TPS peticiones a la vez).

    def on_start(self):
        gevent.sleep(random.random())

    def wait_time(self):
        return max(0.0, 1.0 - (time.time() - getattr(self, "_t_inicio", time.time())))

    @task
    def cotizar(self):
        self._t_inicio = time.time()
        t_rel = time.time() - marcas.get("inicio_ts", time.time())
        fase = fase_de(t_rel)
        idx = random.randrange(N_CON_CACHE if fase == 1 else N_TOTAL)  # fase 1: solo clientes con cache
        t0 = time.time()
        p0 = time.perf_counter()
        with self.client.post(
            "/v1/cotizaciones",
            json={"clienteId": cliente(idx), "productoId": PRODUCTO},
            name="cotizar",
            catch_response=True,
        ) as r:
            ok = r.status_code in (200, 201) and "prima" in (r.text or "")
            if ok:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")
            lat = (time.perf_counter() - p0) * 1000
            filas.append({"ts": iso(t0), "t_rel_s": round(t0 - marcas["inicio_ts"], 3), "fase": fase,
                          "clienteIdx": idx, "status": r.status_code, "ok": int(ok), "latencia_ms": round(lat, 1)})


class Forma(LoadTestShape):
    """TPS usuarios durante F1+F2+F3 segundos y se detiene."""

    def tick(self):
        if self.get_run_time() >= F1 + F2 + F3:
            return None
        return TPS, TPS
