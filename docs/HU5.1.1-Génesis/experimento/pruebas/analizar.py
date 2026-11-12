#!/usr/bin/env python3
"""EXP-010 (HU5.1.1) - analiza una corrida y deja resumen.md, resumen.json y
grafica.png en la carpeta de la corrida.

Cruza dos fuentes:
  1. Lo que vio el socio: codigo de respuesta por caso (resultados.jtl de JMeter
     o resultados.csv del script de Python; mas bypass/resultados.csv).
  2. Lo que vio cada componente: conteos de CloudWatch Logs Insights
     (logs-borde.json, logs-servicios.json, logs-cotizacion.json).

Criterio de la hipotesis: 100 % de codigos esperados en cada caso y ninguna
peticion rechazada registrada en un componente que no debia alcanzar.

  python3 analizar.py <carpeta-de-corrida>
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

ESPERADO = {
    "C1_sin_token": 401,
    "C2_firma_alterada": 401,
    "C3_token_expirado": 401,
    "C4_sin_scope": 403,
    "C5_cliente_de_otro_socio": 403,
    "C6_valida": 201,
    "C7_bypass_sin_borde": 403,
}
QUIEN_RECHAZA = {
    "C1_sin_token": "AWS API Gateway (borde)",
    "C2_firma_alterada": "AWS API Gateway (borde)",
    "C3_token_expirado": "AWS API Gateway (borde)",
    "C4_sin_scope": "AWS API Gateway (borde)",
    "C5_cliente_de_otro_socio": "Distribucion y socios",
    "C6_valida": "- (llega a Cotizacion)",
    "C7_bypass_sin_borde": "api-gateway interno",
}


def leer_filas(carpeta):
    filas = []
    for nombre in ("resultados.jtl", "resultados.csv", os.path.join("bypass", "resultados.csv")):
        ruta = os.path.join(carpeta, nombre)
        if os.path.exists(ruta):
            with open(ruta, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if r.get("label") in ESPERADO:
                        filas.append((r["label"], int(r["responseCode"]) if r["responseCode"].isdigit() else 0))
    return filas


def leer_insights(carpeta, nombre):
    ruta = os.path.join(carpeta, nombre)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    return [{c["field"]: c["value"] for c in fila} for fila in datos.get("results", [])]


def main():
    carpeta = sys.argv[1]
    filas = leer_filas(carpeta)
    if not filas:
        sys.exit("No hay resultados en la carpeta")

    por_caso = defaultdict(Counter)
    for etiqueta, codigo in filas:
        por_caso[etiqueta][codigo] += 1
    n = {c: sum(por_caso[c].values()) for c in ESPERADO}

    tabla, todo_ok = [], True
    for caso, esperado in ESPERADO.items():
        total = n[caso]
        if total == 0:
            continue
        ok = por_caso[caso][esperado]
        pct = 100.0 * ok / total
        todo_ok &= ok == total
        obtenidos = ", ".join(f"{k}x{v}" for k, v in sorted(por_caso[caso].items()))
        tabla.append({"caso": caso, "esperado": esperado, "obtenidos": obtenidos, "aciertos": ok,
                      "total": total, "porcentaje": round(pct, 1), "rechaza": QUIEN_RECHAZA[caso]})

    # ---- Verificacion con logs: que componente vio cada peticion
    verif = []

    def chequear(descripcion, obtenido, esperado):
        nonlocal todo_ok
        cumple = obtenido == esperado
        todo_ok &= cumple
        verif.append({"verificacion": descripcion, "esperado": esperado, "obtenido": obtenido, "cumple": cumple})

    borde = leer_insights(carpeta, "logs-borde.json")
    if borde is not None:
        def b(status, integrado):
            return sum(int(r.get("n", 0)) for r in borde
                       if r.get("status") == str(status) and (r.get("integrationStatus", "-") not in ("-", "")) == integrado)
        chequear("Borde: 401 sin llamar al gateway interno (casos 1-3)", b(401, False),
                 n["C1_sin_token"] + n["C2_firma_alterada"] + n["C3_token_expirado"])
        chequear("Borde: 403 por scope sin llamar al gateway interno (caso 4)", b(403, False), n["C4_sin_scope"])
        chequear("Borde: peticiones reenviadas que terminaron en 403 (caso 5)", b(403, True), n["C5_cliente_de_otro_socio"])
        chequear("Borde: peticiones reenviadas que terminaron en 201 (caso 6)", b(201, True), n["C6_valida"])

    serv = leer_insights(carpeta, "logs-servicios.json")
    if serv is not None:
        def s(servicio, evento, motivo=None):
            return sum(int(r.get("n", 0)) for r in serv if r.get("servicio") == servicio
                       and r.get("evento") == evento and (motivo is None or r.get("motivo") == motivo))
        pasaron = n["C5_cliente_de_otro_socio"] + n["C6_valida"]
        chequear("Gateway interno: peticiones recibidas desde el borde (solo casos 5 y 6)", s("api-gateway", "reenviada"), pasaron)
        chequear("Gateway interno: bypass rechazado por falta del secreto de origen",
                 s("api-gateway", "rechazada", "no_paso_por_gateway_de_borde"), n["C7_bypass_sin_borde"])
        chequear("Distribucion y socios: peticiones recibidas (solo casos 5 y 6)", s("distribucion-socios", "peticion_recibida"), pasaron)
        chequear("Distribucion y socios: 403 por cliente de otro socio (caso 5)",
                 s("distribucion-socios", "rechazada", "cliente_de_otro_socio"), n["C5_cliente_de_otro_socio"])
        chequear("Distribucion y socios: llamadas a Cotizacion (solo caso 6)",
                 s("distribucion-socios", "cotizacion_respondida"), n["C6_valida"])

    cot = leer_insights(carpeta, "logs-cotizacion.json")
    if cot is not None:
        chequear("Cotizacion: POST /cotizaciones recibidos (solo caso 6)",
                 sum(int(r.get("n", 0)) for r in cot), n["C6_valida"])

    faltan = [c for c in ESPERADO if c != "C7_bypass_sin_borde" and n[c] == 0]
    if faltan:  # p. ej. corrida local: los casos 1-4 solo existen con el borde en AWS
        veredicto = "SIN VEREDICTO (corrida parcial, faltan " + ", ".join(faltan) + ")"
    else:
        veredicto = "CONFIRMADA" if todo_ok else "REFUTADA"
    resumen = {"veredicto": veredicto, "casos": tabla, "verificacion_logs": verif}
    with open(os.path.join(carpeta, "resumen.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    md = ["# EXP-010 · Resumen de la corrida", "",
          f"**Hipótesis: {veredicto}** (criterio: 100 % de códigos esperados y ninguna petición rechazada "
          "registrada en un componente que no debía alcanzar).", "",
          "## Respuestas por caso", "",
          "| Caso | Esperado | Obtenidos | Aciertos | % | Quién rechaza |", "|---|---|---|---|---|---|"]
    md += [f"| {t['caso']} | {t['esperado']} | {t['obtenidos']} | {t['aciertos']}/{t['total']} | {t['porcentaje']} | {t['rechaza']} |" for t in tabla]
    if verif:
        md += ["", "## Verificación con CloudWatch Logs", "", "| Verificación | Esperado | Obtenido | Cumple |", "|---|---|---|---|"]
        md += [f"| {v['verificacion']} | {v['esperado']} | {v['obtenido']} | {'sí' if v['cumple'] else 'NO'} |" for v in verif]
    else:
        md += ["", "_Sin logs de CloudWatch (corrida local o 05-recolectar-logs.sh no ejecutado)._"]
    with open(os.path.join(carpeta, "resumen.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        casos = [t["caso"] for t in tabla]
        aciertos = [t["aciertos"] for t in tabla]
        fallos = [t["total"] - t["aciertos"] for t in tabla]
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.barh(casos, aciertos, color="#2e7d32", label="Código esperado")
        ax.barh(casos, fallos, left=aciertos, color="#c62828", label="Código distinto")
        for i, t in enumerate(tabla):
            ax.text(t["total"] + 0.3, i, f"{t['esperado']} · {t['porcentaje']}%", va="center", fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("Peticiones")
        ax.set_title(f"EXP-010 · respuestas por caso · hipótesis {veredicto.split(' (')[0].lower()}")
        ax.legend(loc="lower right", fontsize=8)
        ax.set_xlim(0, max(t["total"] for t in tabla) * 1.35)
        fig.tight_layout()
        fig.savefig(os.path.join(carpeta, "grafica.png"), dpi=150)
    except ImportError:
        pass

    print("\n".join(md))


if __name__ == "__main__":
    main()
