"""
EXP-006 (H7.2.1) - Sonda de disponibilidad de escritura de Aurora.

Cada 200 ms abre una conexion NUEVA al endpoint escritor del cluster, inserta
una fila y registra el resultado y la instancia que atendio la escritura.
Con estos registros se calculan, para la conmutacion por error de Aurora:
  t1 = primera escritura fallida tras la inyeccion
  t2 = primera escritura exitosa posterior (en la nueva escritora)

Corre desde la EC2 de carga (misma region): una prueba piloto desde fuera de
AWS mostro falsas detecciones por la latencia de internet.

    python3 sonda.py --salida sonda.csv          # Ctrl+C o SIGTERM para terminar
"""

import argparse
import csv
import os
import signal
import time
from datetime import datetime, timezone

import psycopg

p = argparse.ArgumentParser()
p.add_argument("--salida", required=True)
p.add_argument("--intervalo", type=float, default=0.2)
args = p.parse_args()

CONNINFO = (
    f"host={os.environ['AURORA_WRITER']} port={os.environ.get('DB_PORT', '5432')} dbname=pagos_db "
    f"user={os.environ.get('DB_USER', 'postgres')} password={os.environ['DB_PASSWORD']} "
    f"connect_timeout=2 sslmode={os.environ.get('PGSSLMODE', 'require')}"
)

seguir = True


def detener(*_):
    global seguir
    seguir = False


signal.signal(signal.SIGTERM, detener)
signal.signal(signal.SIGINT, detener)

with psycopg.connect(CONNINFO) as conn:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sonda_failover ("
        " id BIGSERIAL PRIMARY KEY, registrado TIMESTAMPTZ NOT NULL DEFAULT now(),"
        " instancia TEXT)"
    )


def sondear():
    with psycopg.connect(CONNINFO, options="-c statement_timeout=2000") as conn:
        try:
            instancia = conn.execute("SELECT aurora_db_instance_identifier()").fetchone()[0]
        except psycopg.errors.UndefinedFunction:  # PostgreSQL local (sin Aurora)
            conn.rollback()
            instancia = conn.execute("SELECT 'local:' || inet_server_port()").fetchone()[0]
        conn.execute("INSERT INTO sonda_failover (instancia) VALUES (%s)", (instancia,))
    return instancia


with open(args.salida, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ts_utc", "resultado", "latencia_ms", "instancia", "error"])
    while seguir:
        t0 = time.perf_counter()
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        try:
            inst = sondear()
            w.writerow([ts, "OK", round((time.perf_counter() - t0) * 1000), inst, ""])
        except Exception as e:  # noqa: BLE001 - se registra cualquier falla
            err = f"{type(e).__name__}: {str(e).strip().splitlines()[0][:120] if str(e).strip() else ''}"
            w.writerow([ts, "FALLA", round((time.perf_counter() - t0) * 1000), "", err])
        f.flush()
        time.sleep(max(0.0, args.intervalo - (time.perf_counter() - t0)))
