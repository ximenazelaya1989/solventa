"""
EXP-006 (H7.2.1) - Analisis de una corrida.

Lee los archivos que deja ejecutar_corrida.sh en la carpeta de la corrida y
calcula las variables dependientes del diseno:
  - disponibilidad = ordenes completadas (201) / ordenes enviadas   (k6.csv)
  - transacciones confirmadas perdidas y pagos duplicados           (verificacion.json)
  - por cada falla inyectada (inyecciones.csv):
      t0 = inyeccion, t1 = primera deteccion, t2 = primera recuperacion
      deteccion = t1 - t0, recuperacion = t2 - t0
      * caida de Pagos: t1 = primer error que recibe Siniestros,
        t2 = primera orden completada por reintento   (siniestros-eventos.jsonl)
      * failover de Aurora: t1 = primera escritura fallida de la sonda,
        t2 = primera escritura exitosa posterior     (sonda.csv)
  - latencia p50/p95/p99 de las ordenes
Escribe resumen.json, resumen.md y grafica.png, y evalua la hipotesis H1.

    python3 analizar.py ~/resultados/tacticas-1
"""

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CRITERIO_DISP = 99.99      # %
CRITERIO_TIEMPO = 60.0     # s (deteccion y recuperacion)
VENTANA = 180.0            # s despues de la inyeccion para buscar t1 y t2

carpeta = Path(sys.argv[1]).expanduser()


def ts(valor: str) -> float:
    """Convierte ISO-8601 o epoch (s) a epoch en segundos."""
    valor = valor.strip()
    try:
        return float(valor)
    except ValueError:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).timestamp()


def iso(epoch):
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="milliseconds")


def percentil(valores, p):
    if not valores:
        return None
    v = sorted(valores)
    k = (len(v) - 1) * p / 100
    i = int(k)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (k - i)


def leer_csv(nombre):
    ruta = carpeta / nombre
    if not ruta.exists():
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def leer_jsonl(nombre):
    ruta = carpeta / nombre
    if not ruta.exists():
        return []
    filas = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            try:
                filas.append(json.loads(linea))
            except json.JSONDecodeError:
                pass
    return sorted(filas, key=lambda e: e.get("ts", ""))


# ---------------------------------------------------------------- k6
solicitudes = []  # (epoch_fin, status, duracion_ms)
descartadas = 0
for fila in leer_csv("k6.csv"):
    if fila["metric_name"] == "http_req_duration" and fila.get("name") == "indemnizacion":
        estado = int(float(fila.get("status") or 0))
        solicitudes.append((ts(fila["timestamp"]), estado, float(fila["metric_value"])))
    elif fila["metric_name"] == "dropped_iterations":
        descartadas += int(float(fila["metric_value"]))

enviadas = len(solicitudes) + descartadas
completadas = sum(1 for _, s, _ in solicitudes if s == 201)
fallidas = enviadas - completadas
disponibilidad = 100.0 * completadas / enviadas if enviadas else 0.0
duraciones = [d for _, _, d in solicitudes]
codigos = Counter(s for _, s, _ in solicitudes)

# ---------------------------------------------------------------- verificacion
verif = {}
if (carpeta / "verificacion.json").exists():
    verif = json.loads((carpeta / "verificacion.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- fallas
inyecciones = [(ts(f["ts_utc"]), f["evento"], f.get("detalle", "")) for f in leer_csv("inyecciones.csv")]
eventos = leer_jsonl("siniestros-eventos.jsonl")
sonda = [(ts(f["ts_utc"]), f["resultado"], f.get("instancia", ""), f.get("error", "")) for f in leer_csv("sonda.csv")]


def primero(lista, condicion):
    return next((x for x in lista if condicion(x)), None)


fallas = []
for t0, evento, detalle in inyecciones:
    r = {"evento": evento, "detalle": detalle, "t0": iso(t0)}
    if evento == "caida_pagos":
        ev = [(ts(e["ts"]), e) for e in eventos]
        f1 = primero(ev, lambda x: x[0] >= t0 and x[0] <= t0 + VENTANA and x[1]["evento"] == "intento_fallido")
        t1 = f1[0] if f1 else None
        f2 = primero(ev, lambda x: t1 is not None and x[0] >= t1 and x[1]["evento"] == "pago_confirmado"
                     and x[1].get("intentos", 1) > 1) if t1 else None
        t2 = f2[0] if f2 else None
        afectadas = {e["clave"] for t, e in ev if t0 <= t <= t0 + VENTANA and e["evento"] == "intento_fallido"}
        r.update(fuente="Siniestros (CloudWatch)", ordenes_afectadas=len(afectadas))
    else:  # failover_aurora
        f1 = primero(sonda, lambda x: x[0] >= t0 and x[0] <= t0 + VENTANA and x[1] == "FALLA")
        t1 = f1[0] if f1 else None
        f2 = primero(sonda, lambda x: t1 is not None and x[0] >= t1 and x[1] == "OK") if t1 else None
        t2 = f2[0] if f2 else None
        antes = primero(reversed(sonda), lambda x: x[0] < t0 and x[1] == "OK")
        r.update(fuente="sonda 200 ms", escritora_antes=antes[2] if antes else None,
                 escritora_despues=f2[2] if f2 else None,
                 escrituras_fallidas=sum(1 for x in sonda if t0 <= x[0] <= t0 + VENTANA and x[1] == "FALLA"))
        # Referencia secundaria: lo que vio Siniestros
        ev = [(ts(e["ts"]), e) for e in eventos]
        g1 = primero(ev, lambda x: x[0] >= t0 and x[0] <= t0 + VENTANA and x[1]["evento"] == "intento_fallido")
        r["ordenes_afectadas"] = len({e["clave"] for t, e in ev
                                      if t0 <= t <= t0 + VENTANA and e["evento"] == "intento_fallido"})
        r["siniestros_primer_error"] = iso(g1[0]) if g1 else None
    r.update(t1=iso(t1), t2=iso(t2),
             deteccion_s=round(t1 - t0, 3) if t1 else None,
             recuperacion_s=round(t2 - t0, 3) if t2 else None)
    fallas.append(r)

# ---------------------------------------------------------------- hipotesis
perdidas = verif.get("transacciones_confirmadas_perdidas")
duplicados = verif.get("siniestros_con_pago_duplicado")
tiempos_ok = all(
    (f["deteccion_s"] is None or f["deteccion_s"] <= CRITERIO_TIEMPO)
    and (f["recuperacion_s"] is None or f["recuperacion_s"] <= CRITERIO_TIEMPO)
    for f in fallas
)
criterios = {
    f"disponibilidad >= {CRITERIO_DISP} %": disponibilidad >= CRITERIO_DISP,
    "cero transacciones confirmadas perdidas": perdidas == 0,
    "cero pagos duplicados": duplicados == 0,
    f"deteccion y recuperacion <= {CRITERIO_TIEMPO:.0f} s": tiempos_ok,
}
corrida = {}
if (carpeta / "corrida.json").exists():
    corrida = json.loads((carpeta / "corrida.json").read_text(encoding="utf-8"))

resumen = {
    "corrida": corrida,
    "ordenes": {
        "enviadas": enviadas, "completadas": completadas, "fallidas": fallidas,
        "descartadas_por_k6": descartadas, "codigos_http": dict(codigos),
        "disponibilidad_pct": round(disponibilidad, 4),
    },
    "latencia_ms": {
        "p50": percentil(duraciones, 50), "p95": percentil(duraciones, 95),
        "p99": percentil(duraciones, 99), "max": max(duraciones) if duraciones else None,
    },
    "verificacion": {k: v for k, v in verif.items() if k != "ejemplos"},
    "fallas": fallas,
    "reintentos": {
        "ordenes_con_reintento": len({e["clave"] for e in eventos
                                      if e["evento"] == "pago_confirmado" and e.get("intentos", 1) > 1}),
        "intentos_fallidos": sum(1 for e in eventos if e["evento"] == "intento_fallido"),
        "fallidas_definitivas": sum(1 for e in eventos if e["evento"] == "pago_fallido_definitivo"),
        "max_intentos": max((e.get("intentos", 1) for e in eventos if e["evento"] == "pago_confirmado"), default=None),
    },
    "criterios": criterios,
    "hipotesis_h1": "ACEPTADA" if all(criterios.values()) else "REFUTADA",
}
(carpeta / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------------------------------------------------------------- resumen.md
def fmt(v, suf=""):
    return "n/a" if v is None else (f"{v:.1f}{suf}" if isinstance(v, float) else f"{v}{suf}")


md = [f"# Resultados de la corrida `{corrida.get('nombre', carpeta.name)}`", ""]
md += [f"- Modo: RETRY_IDEMPOTENCY_ENABLED = **{corrida.get('retry_idempotency_enabled', '?')}**",
       f"- Inicio: {corrida.get('inicio', '?')} | Fin: {corrida.get('fin', '?')}", ""]
md += ["## Ordenes de pago", "", "| Métrica | Valor |", "|---|---|",
       f"| Enviadas | {enviadas} |", f"| Completadas (201) | {completadas} |",
       f"| Fallidas | {fallidas} |", f"| **Disponibilidad** | **{disponibilidad:.3f} %** |",
       f"| Latencia p50 / p95 / p99 | {fmt(resumen['latencia_ms']['p50'], ' ms')} / "
       f"{fmt(resumen['latencia_ms']['p95'], ' ms')} / {fmt(resumen['latencia_ms']['p99'], ' ms')} |",
       f"| Órdenes completadas con reintento | {resumen['reintentos']['ordenes_con_reintento']} |", ""]
md += ["## Integridad del dinero", "", "| Métrica | Valor |", "|---|---|",
       f"| Transacciones confirmadas perdidas | {fmt(perdidas)} |",
       f"| Siniestros con pago duplicado | {fmt(duplicados)} |",
       f"| Pagos huérfanos (pagados sin confirmación) | {fmt(verif.get('pagos_huerfanos'))} |",
       f"| Pagos por réplica | {verif.get('pagos_por_replica', {})} |", ""]
md += ["## Fallas inyectadas", "", "| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |",
       "|---|---|---|---|---|---|"]
for f in fallas:
    md.append(f"| {f['evento']} ({f['detalle']}) | {f['t0']} | {fmt(f['deteccion_s'], ' s')} | "
              f"{fmt(f['recuperacion_s'], ' s')} | {f.get('ordenes_afectadas', 'n/a')} | {f['fuente']} |")
for f in fallas:
    if f["evento"] == "failover_aurora":
        md.append(f"\nEscritora de Aurora: `{f.get('escritora_antes')}` → `{f.get('escritora_despues')}` "
                  f"({f.get('escrituras_fallidas')} escrituras fallidas de la sonda).")
md += ["", "## Hipótesis H1", "", "| Criterio | Cumple |", "|---|---|"]
md += [f"| {k} | {'sí' if v else '**no**'} |" for k, v in criterios.items()]
md += ["", f"**H1 {resumen['hipotesis_h1']}**", ""]
(carpeta / "resumen.md").write_text("\n".join(md), encoding="utf-8")

# ---------------------------------------------------------------- grafica
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if solicitudes:
        base = min(t for t, _, _ in solicitudes)
        ok_s, ko_s = Counter(), Counter()
        for t, s, _ in solicitudes:
            (ok_s if s == 201 else ko_s)[int(t - base)] += 1
        segs = range(0, int(max(t for t, _, _ in solicitudes) - base) + 1)
        fig, ejes = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                 gridspec_kw={"height_ratios": [3, 2]})
        ax = ejes[0]
        ax.bar(segs, [ok_s[s] for s in segs], width=1.0, color="#3f63b8", label="completadas (201)")
        ax.bar(segs, [ko_s[s] for s in segs], width=1.0, bottom=[ok_s[s] for s in segs],
               color="#d1495b", label="fallidas")
        ax.set_ylabel("órdenes por segundo")
        ax.set_title(f"{corrida.get('nombre', carpeta.name)} - disponibilidad {disponibilidad:.3f} %")
        ax2 = ejes[1]
        if sonda:
            xs = [x[0] - base for x in sonda]
            ax2.scatter([x for x, s in zip(xs, sonda) if s[1] == "OK"], [1] * sum(1 for s in sonda if s[1] == "OK"),
                        s=2, color="#3f63b8", label="escritura OK")
            ax2.scatter([x for x, s in zip(xs, sonda) if s[1] != "OK"], [0] * sum(1 for s in sonda if s[1] != "OK"),
                        s=8, color="#d1495b", label="escritura fallida")
            ax2.set_yticks([0, 1], ["falla", "ok"])
        ax2.set_ylabel("sonda Aurora (200 ms)")
        ax2.set_xlabel("segundos desde el inicio de la carga")
        for t0, evento, _ in inyecciones:
            for a in ejes:
                a.axvline(t0 - base, color="#b9770e", linestyle="--")
            ejes[0].text(t0 - base + 3, ejes[0].get_ylim()[1] * 0.9, evento, color="#7a4d00")
        ejes[0].legend(loc="lower left")
        ax2.legend(loc="lower left")
        fig.tight_layout()
        fig.savefig(carpeta / "grafica.png", dpi=130)
except ImportError:
    print("matplotlib no instalado: se omite la grafica")

print("\n".join(md))
