"""
Experimento HU2.1.1 · Consolidación de corridas.

Lee resultados/*.json (uno por corrida), promedia las repeticiones de cada
nivel y produce:
  - analisis/tabla-resultados.csv  (tabla por nivel, formato del documento de Ejecución)
  - analisis/fig-latencia.png      (p95/p99 vs nivel, con umbrales del ASR)
  - analisis/fig-error.png         (tasa de error vs nivel)
  - analisis/fig-throughput.png    (throughput logrado vs objetivo)

Uso:  python analisis/consolidar.py resultados
Requiere: pip install matplotlib
"""
import csv
import glob
import json
import os
import statistics
import sys

ORDEN = ["smoke", "carga-baja", "carga-media", "operacion-normal",
         "carga-alta", "carga-muy-alta", "estres"]
P95_ASR, P99_ASR = 1500, 3000
ERROR_MAX_PCT = 1.0  # condición de validez: con más errores, las latencias de las exitosas no son representativas


def promedio(valores):
    valores = [v for v in valores if v is not None]
    return statistics.mean(valores) if valores else None


def main(carpeta):
    corridas = [json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(carpeta, "*.json"))]
    if not corridas:
        sys.exit(f"No hay archivos .json en {carpeta}")
    niveles = sorted({c["nivel"] for c in corridas},
                     key=lambda n: ORDEN.index(n) if n in ORDEN else 99)

    filas = []
    for nivel in niveles:
        grupo = [c for c in corridas if c["nivel"] == nivel]
        aprob = [c["latencia"]["aprobada"] or {} for c in grupo]
        p95s = [a.get("p95") for a in aprob]
        fila = {
            "nivel": nivel,
            "tps_objetivo": grupo[0]["tpsObjetivo"],
            "repeticiones": len(grupo),
            "p95_ms": promedio(p95s),
            "p99_ms": promedio([a.get("p99") for a in aprob]),
            "promedio_ms": promedio([a.get("promedio") for a in aprob]),
            "min_ms": min((a.get("minimo") for a in aprob if a.get("minimo") is not None), default=None),
            "max_ms": max((a.get("maximo") for a in aprob if a.get("maximo") is not None), default=None),
            "desviacion_ms": promedio([a.get("desviacion") for a in aprob]),
            "desv_p95_entre_reps_ms": statistics.stdev([p for p in p95s if p is not None]) if len(grupo) > 1 else 0,
            "throughput_req_s": promedio([c["throughput"] for c in grupo]),
            "error_pct": 100 * (promedio([c["tasaError"] for c in grupo]) or 0),
            "descartadas": sum(c["iteracionesDescartadas"] for c in grupo),
        }
        fila["cumple_asr"] = ((fila["p95_ms"] or 1e9) < P95_ASR and (fila["p99_ms"] or 1e9) < P99_ASR
                             and fila["error_pct"] < ERROR_MAX_PCT)
        filas.append(fila)

    salida = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(salida, "tabla-resultados.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        for fila in filas:
            w.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in fila.items()})

    inflexion = [f["nivel"] for f in filas if f["cumple_asr"]]
    print(f"{'Nivel':<18}{'TPS':>6}{'reps':>6}{'p95':>10}{'p99':>10}{'thr':>9}{'err%':>8}  ASR")
    for f in filas:
        print(f"{f['nivel']:<18}{f['tps_objetivo']:>6}{f['repeticiones']:>6}"
              f"{(f['p95_ms'] or 0):>10.1f}{(f['p99_ms'] or 0):>10.1f}"
              f"{(f['throughput_req_s'] or 0):>9.1f}{f['error_pct']:>8.2f}  {'sí' if f['cumple_asr'] else 'NO'}")
    print(f"\nÚltimo nivel que cumple el ASR (punto de inflexión): {inflexion[-1] if inflexion else 'ninguno'}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no está instalado: se omiten las figuras (pip install matplotlib)")
        return

    x = [f"{f['nivel']}\n({f['tps_objetivo']} TPS)" for f in filas]

    plt.figure(figsize=(10, 5))
    plt.plot(x, [f["p99_ms"] for f in filas], marker="o", label="p99")
    plt.plot(x, [f["p95_ms"] for f in filas], marker="o", label="p95")
    plt.axhline(P95_ASR, linestyle="--", color="tab:orange", label="Umbral p95 = 1500 ms")
    plt.axhline(P99_ASR, linestyle="--", color="tab:red", label="Umbral p99 = 3000 ms")
    plt.ylabel("Latencia (ms)")
    plt.title("POST /suscripciones (aprobación automática) — p95/p99 vs nivel de carga")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(salida, "fig-latencia.png"), dpi=150); plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(x, [f["error_pct"] for f in filas], marker="o", color="tab:red")
    plt.ylabel("Tasa de error (%)")
    plt.title("POST /suscripciones — tasa de error vs nivel de carga")
    plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(salida, "fig-error.png"), dpi=150); plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(x, [f["throughput_req_s"] for f in filas], marker="o", label="Throughput logrado")
    plt.plot(x, [f["tps_objetivo"] for f in filas], linestyle="--", label="Carga ofrecida (TPS objetivo)")
    plt.ylabel("req/s")
    plt.title("POST /suscripciones — throughput logrado vs carga ofrecida")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(salida, "fig-throughput.png"), dpi=150); plt.close()
    print(f"Figuras guardadas en {salida}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "resultados")
