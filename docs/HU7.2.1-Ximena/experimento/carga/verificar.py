"""
EXP-006 (H7.2.1) - Verificacion de perdidas y duplicados.

Cruza las confirmaciones que recibio Siniestros (siniestros en estado PAGADO,
en siniestros_db) con los pagos registrados en Pagos (pagos_db en Aurora):
  - perdidas:   confirmadas por Pagos pero sin pago procesado en pagos_db
  - duplicados: siniestros con mas de un pago en pagos_db
  - huerfanos:  pagos procesados cuyo siniestro no recibio la confirmacion
                (Pagos pago, pero la respuesta no llego a Siniestros)

    python3 verificar.py --salida verificacion.json
"""

import argparse
import json
import os

import psycopg

p = argparse.ArgumentParser()
p.add_argument("--salida", required=True)
args = p.parse_args()


def conectar(host, db, puerto=None):
    return psycopg.connect(
        host=host, dbname=db, user=os.environ.get("DB_USER", "postgres"),
        password=os.environ["DB_PASSWORD"], sslmode=os.environ.get("PGSSLMODE", "require"),
        port=int(puerto or os.environ.get("DB_PORT", 5432)), connect_timeout=5,
    )


with conectar(os.environ["SINIESTROS_DB"], "siniestros_db", os.environ.get("SINIESTROS_DB_PORT")) as c:
    siniestros = c.execute(
        'SELECT id::text, estado::text, "claveIdempotenciaPago", "pagoId"::text, "intentosPago" '
        "FROM siniestros"
    ).fetchall()

with conectar(os.environ["AURORA_WRITER"], "pagos_db") as c:
    pagos = c.execute(
        'SELECT id::text, "claveIdempotencia", "siniestroId"::text, estado::text, "atendidoPor" '
        "FROM pagos"
    ).fetchall()

confirmados = {s[2]: s for s in siniestros if s[1] == "pagado"}
sin_confirmar = {s[2]: s for s in siniestros if s[1] != "pagado"}
pagos_por_clave = {}
pagos_por_siniestro = {}
for pg in pagos:
    pagos_por_clave.setdefault(pg[1], []).append(pg)
    pagos_por_siniestro.setdefault(pg[2], []).append(pg)

perdidas = [k for k in confirmados if not any(x[3] == "procesado" for x in pagos_por_clave.get(k, []))]
duplicados = {sid: len(v) for sid, v in pagos_por_siniestro.items() if len(v) > 1}
huerfanos = [k for k in sin_confirmar if any(x[3] == "procesado" for x in pagos_por_clave.get(k, []))]
pendientes = [pg[1] for pg in pagos if pg[3] == "pendiente"]

replicas = {}
for pg in pagos:
    replicas[pg[4] or "?"] = replicas.get(pg[4] or "?", 0) + 1

resultado = {
    "siniestros_registrados": len(siniestros),
    "confirmados_por_pagos": len(confirmados),
    "no_confirmados": len(sin_confirmar),
    "pagos_registrados": len(pagos),
    "pagos_procesados": sum(1 for pg in pagos if pg[3] == "procesado"),
    "pagos_pendientes": len(pendientes),
    "transacciones_confirmadas_perdidas": len(perdidas),
    "siniestros_con_pago_duplicado": len(duplicados),
    "pagos_huerfanos": len(huerfanos),
    "pagos_por_replica": replicas,
    "ejemplos": {
        "perdidas": perdidas[:10],
        "duplicados": list(duplicados.items())[:10],
        "huerfanos": huerfanos[:10],
    },
}
with open(args.salida, "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print(json.dumps({k: v for k, v in resultado.items() if k != "ejemplos"}, indent=2, ensure_ascii=False))
