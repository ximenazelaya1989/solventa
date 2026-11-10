"""
EXP-006 (H7.2.1) - Tabla comparativa de todas las corridas (con tacticas vs
prueba de control) a partir de los resumen.json de cada carpeta.

    python3 comparar.py ~/resultados
Escribe comparacion.md y comparacion.png en esa carpeta.
"""

import json
import sys
from pathlib import Path

raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "~/resultados").expanduser()
filas = []
for r in sorted(raiz.glob("*/resumen.json")):
    d = json.loads(r.read_text(encoding="utf-8"))
    fallas = {f["evento"]: f for f in d["fallas"]}
    filas.append({
        "corrida": r.parent.name,
        "modo": "tácticas" if d["corrida"].get("retry_idempotency_enabled") == "true" else "control",
        "enviadas": d["ordenes"]["enviadas"],
        "completadas": d["ordenes"]["completadas"],
        "disp": d["ordenes"]["disponibilidad_pct"],
        "perdidas": d["verificacion"].get("transacciones_confirmadas_perdidas"),
        "duplicados": d["verificacion"].get("siniestros_con_pago_duplicado"),
        "huerfanos": d["verificacion"].get("pagos_huerfanos"),
        "det_pagos": fallas.get("caida_pagos", {}).get("deteccion_s"),
        "rec_pagos": fallas.get("caida_pagos", {}).get("recuperacion_s"),
        "det_aurora": fallas.get("failover_aurora", {}).get("deteccion_s"),
        "rec_aurora": fallas.get("failover_aurora", {}).get("recuperacion_s"),
        "p99": d["latencia_ms"]["p99"],
        "h1": d["hipotesis_h1"],
    })

f = lambda v, n=1: "n/a" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else str(v))
md = ["# Comparación de corridas - EXP-006 (H7.2.1)", "",
      "| Corrida | Modo | Enviadas | Completadas | Disponibilidad | Perdidas | Duplicados | Huérfanos | "
      "Caída Pagos det./rec. (s) | Failover Aurora det./rec. (s) | p99 (ms) | H1 |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for x in filas:
    md.append(f"| {x['corrida']} | {x['modo']} | {x['enviadas']} | {x['completadas']} | {x['disp']:.3f} % | "
              f"{f(x['perdidas'])} | {f(x['duplicados'])} | {f(x['huerfanos'])} | "
              f"{f(x['det_pagos'])} / {f(x['rec_pagos'])} | {f(x['det_aurora'])} / {f(x['rec_aurora'])} | "
              f"{f(x['p99'], 0)} | {x['h1']} |")
(raiz / "comparacion.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if filas:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        colores = ["#3f63b8" if x["modo"] == "tácticas" else "#d1495b" for x in filas]
        ax.bar([x["corrida"] for x in filas], [x["disp"] for x in filas], color=colores)
        ax.axhline(99.99, color="#b9770e", linestyle="--", label="criterio 99,99 %")
        ax.set_ylim(min(x["disp"] for x in filas) - 0.5, 100.05)
        ax.set_ylabel("disponibilidad (%)")
        ax.set_title("Disponibilidad del desembolso: con tácticas (azul) vs control (rojo)")
        for i, x in enumerate(filas):
            ax.text(i, x["disp"], f"{x['disp']:.2f}", ha="center", va="bottom", fontsize=9)
        ax.legend()
        fig.tight_layout()
        fig.savefig(raiz / "comparacion.png", dpi=130)
except ImportError:
    pass
