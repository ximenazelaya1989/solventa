"""EXP-009: calcula las metricas del experimento a partir de una corrida de Locust.

Lee <carpeta>/requests.csv y <carpeta>/estado_final.json y escribe
<carpeta>/resumen.json y <carpeta>/resumen.md:

  - disponibilidad por fase (cotizaciones con precio / total) y criterio <= 0,1 % de fallos en la fase 2
  - p95 y p99 de latencia por fase
  - tiempo de deteccion: falla inyectada -> circuito ABIERTO (de la ultima tarea de Perfilamiento)
  - tiempo de recuperacion: Open Finance restaurado -> circuito CERRADO (de la ultima tarea)
  - % servido desde cache y % con perfil por defecto

Uso:  python analizar.py resultados/B1
"""
from __future__ import annotations  # compatibilidad con Python 3.9 (EC2 de Amazon Linux 2023)

import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path


def pct(valores: list[float], p: float) -> float | None:
    if not valores:
        return None
    s = sorted(valores)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)]  # percentil por rango mas cercano


def t(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def main(carpeta: Path) -> None:
    filas = list(csv.DictReader(open(carpeta / "requests.csv", encoding="utf8")))
    estado = json.loads((carpeta / "estado_final.json").read_text(encoding="utf8"))
    cfg, marcas = estado["config"], estado["marcas"]

    nombres = {"1": "1 normal", "2": "2 falla", "3": "3 recuperacion"}
    fases = {}
    for f in ("1", "2", "3"):
        x = [r for r in filas if r["fase"] == f]
        lat = [float(r["latencia_ms"]) for r in x]
        ok = sum(int(r["ok"]) for r in x)
        fases[nombres[f]] = {
            "solicitudes": len(x), "exitosas": ok, "fallos": len(x) - ok,
            "disponibilidad_pct": round(100 * ok / len(x), 3) if x else None,
            "p95_ms": pct(lat, 95), "p99_ms": pct(lat, 99),
        }

    total = len(filas)
    ok_total = sum(int(r["ok"]) for r in filas)
    f2 = fases[nombres["2"]]
    maximo_fallos_f2 = math.floor(f2["solicitudes"] * 0.001)

    # transiciones del circuito por tarea de Perfilamiento
    deteccion, recuperacion = [], []
    falla_ts = t(marcas["falla_ts"]) if "falla_ts" in marcas else None
    rest_ts = t(marcas["restauracion_ts"]) if "restauracion_ts" in marcas else None
    # Referencia de tiempo: las horas que registra el propio mock al cambiar de modo. Estan en el mismo
    # tipo de reloj que las transiciones del circuito (servidores), a diferencia de la hora de Locust,
    # que puede estar desfasada respecto a ellos.
    cambios = estado["mock"].get("cambios", [])
    idx_falla = max((i for i, c in enumerate(cambios) if c["modo"] != "ok"), default=None)
    if idx_falla is not None:
        falla_ts = t(cambios[idx_falla]["desde"])
        rest = [c for c in cambios[idx_falla + 1:] if c["modo"] == "ok"]
        rest_ts = t(rest[0]["desde"]) if rest else rest_ts
    tareas = estado["perfilamiento"]
    for url, e in tareas.items():
        tr = e.get("transiciones", [])
        abre = [t(x["desde"]) for x in tr if x["estado"] == "ABIERTO" and falla_ts and t(x["desde"]) >= falla_ts]
        cierra = [t(x["desde"]) for x in tr if x["estado"] == "CERRADO" and rest_ts and t(x["desde"]) >= rest_ts]
        if abre:
            deteccion.append(round(min(abre) - falla_ts, 3))
        if cierra:
            recuperacion.append(round(min(cierra) - rest_ts, 3))

    cont = {}
    for e in tareas.values():
        for k, v in e.get("contadores", {}).items():
            cont[k] = cont.get(k, 0) + v
    degradadas = cont.get("servidasDesdeCache", 0) + cont.get("servidasPerfilPorDefecto", 0)

    resumen = {
        "config": {**cfg, "circuitBreakerEnabled": any(e.get("circuitBreakerEnabled") for e in tareas.values())},
        "disponibilidad_total_pct": round(100 * ok_total / total, 3) if total else None,
        "solicitudes_total": total,
        "fases": fases,
        "criterio_fase_falla": {"maximo_fallos_permitidos": maximo_fallos_f2, "fallos": f2["fallos"],
                                "cumple": f2["fallos"] <= maximo_fallos_f2},
        "tiempo_deteccion_s_por_tarea": deteccion,
        "tiempo_deteccion_s_max": max(deteccion) if deteccion else None,
        "tiempo_recuperacion_s_por_tarea": recuperacion,
        "tiempo_recuperacion_s_max": max(recuperacion) if recuperacion else None,
        "servidas_desde_cache_pct": round(100 * cont.get("servidasDesdeCache", 0) / degradadas, 1) if degradadas else None,
        "servidas_perfil_por_defecto_pct": round(100 * cont.get("servidasPerfilPorDefecto", 0) / degradadas, 1) if degradadas else None,
        "contadores_perfilamiento": cont,
        "llamadas_al_mock": estado["mock"].get("llamadasTotal"),
    }
    (carpeta / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf8")

    md = [f"# Resumen de la corrida `{carpeta.name}`", "",
          f"Circuit breaker: **{'activado (B)' if resumen['config']['circuitBreakerEnabled'] else 'apagado (A)'}** · "
          f"modo de falla: `{cfg['modoFalla']}` · {cfg['TPS']} TPS · fases {cfg['F1']}/{cfg['F2']}/{cfg['F3']} s", "",
          f"Disponibilidad total: **{resumen['disponibilidad_total_pct']} %** ({ok_total}/{total})", "",
          "| Fase | Solicitudes | Fallos | Disponibilidad | p95 (ms) | p99 (ms) |", "|---|---:|---:|---:|---:|---:|"]
    for n, v in fases.items():
        md.append(f"| {n} | {v['solicitudes']} | {v['fallos']} | {v['disponibilidad_pct']} % | {v['p95_ms']} | {v['p99_ms']} |")
    c = resumen["criterio_fase_falla"]
    md += ["", f"Criterio de la fase de falla (<= 0,1 % de fallos): {c['fallos']} fallos, maximo {c['maximo_fallos_permitidos']} -> "
               f"**{'CUMPLE' if c['cumple'] else 'NO CUMPLE'}**",
           f"Tiempo de deteccion (falla -> circuito ABIERTO): {resumen['tiempo_deteccion_s_max']} s (meta <= 5 s)",
           f"Tiempo de recuperacion (restauracion -> CERRADO): {resumen['tiempo_recuperacion_s_max']} s",
           f"Servidas desde cache: {resumen['servidas_desde_cache_pct']} % · con perfil por defecto: {resumen['servidas_perfil_por_defecto_pct']} %"]
    (carpeta / "resumen.md").write_text("\n".join(md) + "\n", encoding="utf8")
    print("\n".join(md))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
