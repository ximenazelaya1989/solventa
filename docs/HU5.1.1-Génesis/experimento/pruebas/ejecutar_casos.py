#!/usr/bin/env python3
"""EXP-010 (HU5.1.1) - alternativa a JMeter: corre los 6 casos (20 peticiones
secuenciales cada uno, sin carga) y la prueba de bypass, y deja un CSV con el
mismo formato basico de un .jtl de JMeter mas el requestId del API Gateway.

Uso (AWS):   python3 ejecutar_casos.py --props ../../resultados/tokens.properties --salida corrida/
Uso (local): python3 ejecutar_casos.py --local --salida corrida-local/
  En local no hay AWS API Gateway: se simula el borde agregando los encabezados
  que el pondria (x-origin-verify, x-socio-client-id) y solo se pueden probar
  los casos 5 y 6 y el bypass. Los casos 1 a 4 los resuelve el borde en AWS.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

CLIENTE_A = "11111111-1111-1111-1111-111111111111"
CLIENTE_B = "33333333-3333-3333-3333-333333333333"
PRODUCTO = "22222222-2222-2222-2222-222222222222"

# etiqueta, propiedad del token, cliente, codigo esperado
CASOS = [
    ("C1_sin_token", None, CLIENTE_A, 401),
    ("C2_firma_alterada", "token_alterado", CLIENTE_A, 401),
    ("C3_token_expirado", "token_expirado", CLIENTE_A, 401),
    ("C4_sin_scope", "token_sin_scope", CLIENTE_A, 403),
    ("C5_cliente_de_otro_socio", "token_a", CLIENTE_B, 403),
    ("C6_valida", "token_a", CLIENTE_A, 201),
]


def leer_props(ruta):
    props = {}
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            if "=" in linea and not linea.startswith("#"):
                k, v = linea.rstrip("\n").split("=", 1)
                props[k.strip()] = v.strip()
    return props


def enviar(url, cliente, encabezados):
    cuerpo = json.dumps({"clienteId": cliente, "productoId": PRODUCTO}).encode()
    req = urllib.request.Request(url, data=cuerpo, method="POST",
                                 headers={"content-type": "application/json", **encabezados})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            codigo, cab = r.status, r.headers
    except urllib.error.HTTPError as e:
        codigo, cab = e.code, e.headers
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  error de red: {e}", file=sys.stderr)
        codigo, cab = 0, {}
    return int(t0 * 1000), int((time.time() - t0) * 1000), codigo, (cab.get("apigw-requestid", "") if cab else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--props", help="tokens.properties (de 03-obtener-tokens.sh)")
    ap.add_argument("--salida", required=True, help="carpeta de la corrida")
    ap.add_argument("--peticiones", type=int, default=20)
    ap.add_argument("--bypass", default=None, help="URL del gateway interno para la prueba de bypass")
    ap.add_argument("--local", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)

    if a.local:
        url = "http://localhost:18080/v1/socios/cotizaciones"
        borde = {"x-origin-verify": os.getenv("ORIGIN_VERIFY_SECRET", "secreto-local")}
        props = {"token_a": "local-socio-a", "client_id_a": "local-socio-a"}
        casos = [c for c in CASOS if c[0] in ("C5_cliente_de_otro_socio", "C6_valida")]
        bypass = "http://localhost:18080"
    else:
        props = leer_props(a.props)
        url = f"https://{props['host']}/v1/socios/cotizaciones"
        casos = CASOS
        bypass = a.bypass
        emitido = int(props.get("token_expirado_emitido", "0"))
        espera = emitido + 5 * 60 + 30 - int(time.time())
        if espera > 0:
            print(f"Esperando {espera} s para que el token del caso 3 expire...")
            time.sleep(espera)

    filas = []
    inicio = int(time.time())
    for etiqueta, prop, cliente, esperado in casos:
        if a.local:  # el borde simulado pone la identidad del token ya validado
            enc = {**borde, "x-socio-client-id": props[prop]}
        else:
            enc = {"authorization": f"Bearer {props[prop]}"} if prop else {}
        for _ in range(a.peticiones):
            ts, ms, codigo, rid = enviar(url, cliente, enc)
            filas.append([ts, ms, etiqueta, codigo, str(codigo == esperado).lower(), esperado, rid])
        ok = sum(1 for f in filas if f[2] == etiqueta and f[4] == "true")
        print(f"{etiqueta:28s} esperado {esperado}: {ok}/{a.peticiones}")

    if bypass:  # peticion valida que intenta saltarse el borde
        for _ in range(5):
            ts, ms, codigo, rid = enviar(f"{bypass.rstrip('/')}/v1/socios/cotizaciones", CLIENTE_A,
                                         {"x-socio-client-id": props.get("client_id_a", "local-socio-a")})
            filas.append([ts, ms, "C7_bypass_sin_borde", codigo, str(codigo == 403).lower(), 403, rid])
        ok = sum(1 for f in filas if f[2] == "C7_bypass_sin_borde" and f[4] == "true")
        print(f"{'C7_bypass_sin_borde':28s} esperado 403: {ok}/5")
    fin = int(time.time())

    with open(os.path.join(a.salida, "resultados.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timeStamp", "elapsed", "label", "responseCode", "success", "esperado", "apigwRequestId"])
        w.writerows(filas)
    with open(os.path.join(a.salida, "ventana.json"), "w") as f:
        json.dump({"inicio": inicio, "fin": fin, "peticiones": a.peticiones}, f)
    print(f"Resultados en {a.salida}/resultados.csv")


if __name__ == "__main__":
    main()
