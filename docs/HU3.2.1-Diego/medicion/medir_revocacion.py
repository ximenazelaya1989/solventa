"""EXP-007 - Revocacion efectiva de consentimiento Open Finance (HU3.2.1).

Subcomandos:
  precargar   crea los clientes de MEDICION (se revocan) y de FONDO (para JMeter, nunca se
              revocan): perfil en Perfilamiento + consentimiento vigente en Consentimiento.
  token       imprime un JWT de lector (rol analista, scope perfil:read) para JMeter.
  medir       por cada cliente de medicion: (a) GET perfil -> 200; (b) revoca y toma t0 cuando
              Consentimiento confirma; (c) GET cada --sondeo s hasta el primer 403 = t1;
              (d) sigue consultando --vigilancia s para verificar que no reaparece un 200.
              Los clientes arrancan escalonados (--escalonamiento s) y corren en paralelo, asi
              las revocaciones caen en momentos distintos del ciclo de la cache.
              Al final revisa el audit_log y (opcional) el contador del mock de Open Finance.
  jmeter      analiza el .jtl de JMeter: p95 de GET /perfiles y rechazos a clientes vigentes.

Ejemplo (desde la EC2 de pruebas):
  # Un solo ALB con reglas por ruta: /perfiles* -> Perfilamiento; /consentimientos* y /auditoria* -> Consentimiento
  export JWT_SECRET=...  PERF=https://<dns-del-alb>  CONS=https://<dns-del-alb>
  python medir_revocacion.py precargar --perfilamiento $PERF --consentimiento $CONS --insecure
  jmeter -n -t ../jmeter/carga_fondo.jmx -Jtoken=$(python medir_revocacion.py token) ...
  python medir_revocacion.py medir --perfilamiento $PERF --consentimiento $CONS --insecure
  python medir_revocacion.py jmeter resultados/jmeter.jtl

Los tokens se firman con JWT_SECRET (HS256), la misma llave de los servicios: en el
experimento el script hace el papel del proveedor de identidad (no hay Cognito en AWS Academy).
"""
import argparse
import csv
import json
import os
import statistics
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import httpx
import jwt

UMBRAL_S = 300  # 5 minutos: medida del ASR
AQUI = Path(__file__).resolve().parent


# ---------------- utilidades ----------------


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds")


def token(secret: str, sub: str, rol: str, scope: str, horas: float = 8) -> str:
    claims = {"sub": sub, "rol": rol, "scope": scope, "exp": int(time.time() + horas * 3600)}
    return jwt.encode(claims, secret, algorithm="HS256")


def auth(secret: str, sub: str, rol: str, scope: str) -> dict:
    return {"Authorization": f"Bearer {token(secret, sub, rol, scope)}"}


def p95(valores: list[float]) -> float:
    if not valores:
        return float("nan")
    ordenados = sorted(valores)
    k = max(0, int(round(0.95 * len(ordenados) + 0.5)) - 1)  # metodo nearest-rank
    return ordenados[min(k, len(ordenados) - 1)]


def cliente_http(args) -> httpx.Client:
    verify: bool | str = True
    if args.insecure:
        verify = False  # certificado autofirmado del ALB
    elif args.ca:
        verify = args.ca
    return httpx.Client(timeout=10, verify=verify)


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------- precargar ----------------


def precargar(args) -> None:
    http = cliente_http(args)
    archivo = Path(args.clientes)
    clientes = {
        "medicion": [str(uuid.uuid4()) for _ in range(args.n)],
        "fondo": [str(uuid.uuid4()) for _ in range(args.n_fondo)],
    }
    for grupo, ids in clientes.items():
        for i, cid in enumerate(ids, 1):
            r = http.post(f"{args.perfilamiento}/perfiles", json={"clienteId": cid, "score": 40 + (i % 50)})
            if r.status_code not in (201, 409):
                sys.exit(f"Error creando perfil {cid}: {r.status_code} {r.text}")
            r = http.post(
                f"{args.consentimiento}/consentimientos",
                json={"clienteId": cid, "fuente": "open_finance", "alcance": "senales_financieras"},
                headers=auth(args.secret, cid, "cliente", "consentimiento:write"),
            )
            if r.status_code not in (201, 409):
                sys.exit(f"Error otorgando consentimiento {cid}: {r.status_code} {r.text}")
        log(f"{grupo}: {len(ids)} clientes con perfil y consentimiento vigente")
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(clientes, indent=2))
    csv_fondo = archivo.with_name("clientes_fondo.csv")
    csv_fondo.write_text("clienteId\n" + "\n".join(clientes["fondo"]) + "\n")
    log(f"Guardado {archivo} y {csv_fondo} (este ultimo es el CSV de JMeter)")


# ---------------- medir ----------------


def medir_cliente(args, http: httpx.Client, cid: str, h_lector: dict) -> dict:
    url = f"{args.perfilamiento}/perfiles/{cid}"
    fila = {"clienteId": cid}

    # (a) antes de revocar debe responder 200
    r = http.get(url, headers=h_lector)
    fila["estado_inicial"] = r.status_code
    if r.status_code != 200:
        fila["error"] = f"estado inicial {r.status_code} (rechazo falso)"
        return fila

    # (b) revocar: t0 = cuando Consentimiento confirma
    lista = http.get(
        f"{args.consentimiento}/consentimientos",
        params={"clienteId": cid},
        headers=auth(args.secret, cid, "cliente", "consentimiento:read"),
    ).json()
    activo = next(c for c in lista if c["estado"] == "activo" and c["fuente"] == "open_finance")
    r = http.post(
        f"{args.consentimiento}/consentimientos/{activo['id']}/revocacion",
        headers=auth(args.secret, cid, "cliente", "consentimiento:write"),
    )
    t0 = time.time()
    if r.status_code != 200:
        fila["error"] = f"revocacion respondio {r.status_code}"
        return fila
    fila["t0"] = iso(t0)

    # (c) sondeo hasta el primer 403
    consultas_200 = 0
    otros = 0
    t1 = None
    while time.time() - t0 < UMBRAL_S + 60:
        r = http.get(url, headers=h_lector)
        if r.status_code == 403:
            t1 = time.time()
            break
        if r.status_code == 200:
            consultas_200 += 1
        else:
            otros += 1
        time.sleep(args.sondeo)
    fila["consultas_200_tras_revocar"] = consultas_200
    if t1 is None:
        fila["error"] = "no aparecio 403 dentro del plazo"
        fila["accesos_indebidos"] = consultas_200
        return fila
    fila["t1"] = iso(t1)
    fila["delta_s"] = round(t1 - t0, 3)
    snap_mock = estado_mock(args, http)
    fila["_mock_t1"] = (snap_mock or {}).get(cid)

    # (d) vigilancia: no debe reaparecer un 200
    reaparece = 0
    indebidos = 0  # 200 despues de t0 + 300 s
    fin = t1 + args.vigilancia
    while time.time() < fin:
        time.sleep(args.sondeo_vigilancia)
        r = http.get(url, headers=h_lector)
        if r.status_code == 200:
            reaparece += 1
            if time.time() - t0 > UMBRAL_S:
                indebidos += 1
        elif r.status_code != 403:
            otros += 1
    fila["200_tras_primer_403"] = reaparece
    fila["accesos_indebidos"] = indebidos
    fila["otras_respuestas"] = otros
    return fila


def estado_mock(args, http: httpx.Client) -> dict | None:
    """Contador de llamadas por cliente del mock de Open Finance (si se paso --mock)."""
    if not args.mock:
        return None
    try:
        return http.get(f"{args.mock}/admin/estado").json().get("llamadasPorCliente", {})
    except Exception:
        return None


def medir(args) -> None:
    clientes = json.loads(Path(args.clientes).read_text())["medicion"][: args.n]
    http = cliente_http(args)
    h_lector = auth(args.secret, "script-medicion", "analista", "perfil:read")
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    log(
        f"Midiendo {len(clientes)} clientes: escalonamiento {args.escalonamiento}s, sondeo {args.sondeo}s, "
        f"vigilancia {args.vigilancia}s. Duracion aprox. {(len(clientes) * args.escalonamiento + 70 + args.vigilancia) / 60:.0f} min"
    )

    filas: list[dict] = []
    lock = threading.Lock()

    def tarea(i: int, cid: str):
        time.sleep(i * args.escalonamiento)
        try:
            f = medir_cliente(args, http, cid, h_lector)
        except Exception as e:  # una falla de red no debe tumbar toda la corrida
            f = {"clienteId": cid, "error": repr(e)}
        with lock:
            filas.append(f)
            log(f"{len(filas):>2}/{len(clientes)} {cid[:8]} delta={f.get('delta_s')} indebidos={f.get('accesos_indebidos')} {f.get('error', '')}")

    with ThreadPoolExecutor(max_workers=len(clientes)) as pool:
        for i, cid in enumerate(clientes):
            pool.submit(tarea, i, cid)

    # Mock de Open Finance: el contador no debe subir despues del primer 403
    snap_final = estado_mock(args, http)
    for f in filas:
        if snap_final is not None and "_mock_t1" in f:
            antes = f.pop("_mock_t1") or 0
            f["llamadas_open_finance_tras_403"] = (snap_final.get(f["clienteId"]) or 0) - antes
        else:
            f.pop("_mock_t1", None)

    # audit_log: una revocacion registrada por cliente
    aud = http.get(
        f"{args.consentimiento}/auditoria",
        params={"evento": "REVOCADO", "desde": iso(inicio), "limite": 5000},
        headers=auth(args.secret, "auditor-exp007", "auditor", "auditoria:read"),
    ).json()
    revocados_auditados = {a["clienteId"] for a in aud} & set(clientes)
    for f in filas:
        f["revocacion_en_audit_log"] = f["clienteId"] in revocados_auditados

    # CSV detallado
    columnas = [
        "clienteId", "estado_inicial", "t0", "t1", "delta_s", "consultas_200_tras_revocar",
        "200_tras_primer_403", "accesos_indebidos", "otras_respuestas",
        "llamadas_open_finance_tras_403", "revocacion_en_audit_log", "error",
    ]
    with open(salida / "revocaciones.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(filas, key=lambda f: f.get("t0", "")))

    deltas = [f["delta_s"] for f in filas if "delta_s" in f]
    resumen = {
        "fecha": iso(inicio),
        "clientes": len(clientes),
        "revocaciones_medidas": len(deltas),
        "delta_s": {
            "min": min(deltas, default=None),
            "promedio": round(statistics.mean(deltas), 3) if deltas else None,
            "p95": p95(deltas) if deltas else None,
            "max": max(deltas, default=None),
        },
        "accesos_indebidos_despues_de_5_min": sum(f.get("accesos_indebidos", 0) for f in filas),
        "200_tras_primer_403": sum(f.get("200_tras_primer_403", 0) for f in filas),
        "rechazos_falsos_antes_de_revocar": sum(1 for f in filas if f.get("estado_inicial") not in (200, None)),
        "revocaciones_en_audit_log": f"{len(revocados_auditados)}/{len(clientes)}",
        "llamadas_open_finance_tras_403": (
            sum(f.get("llamadas_open_finance_tras_403", 0) for f in filas) if snap_final is not None else "sin --mock"
        ),
        "errores": [f"{f['clienteId']}: {f['error']}" for f in filas if f.get("error")],
    }
    resumen["criterio"] = {
        "delta_max_<=_300s": bool(deltas) and len(deltas) == len(clientes) and max(deltas) <= UMBRAL_S,
        "0_accesos_indebidos": resumen["accesos_indebidos_despues_de_5_min"] == 0,
        "0_rechazos_falsos_(script)": resumen["rechazos_falsos_antes_de_revocar"] == 0,
        "audit_log_completo": len(revocados_auditados) == len(clientes),
        "p95_latencia": "ver subcomando jmeter",
    }
    (salida / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False))
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    log(f"Resultados en {salida}/revocaciones.csv y {salida}/resumen.json")


# ---------------- jmeter ----------------


def analizar_jmeter(args) -> None:
    lat, codigos = [], {}
    with open(args.jtl, newline="") as fh:
        for fila in csv.DictReader(fh):
            lat.append(int(fila["elapsed"]))
            codigos[fila["responseCode"]] = codigos.get(fila["responseCode"], 0) + 1
    total = len(lat)
    resumen = {
        "solicitudes": total,
        "codigos": codigos,
        "latencia_ms": {"p50": statistics.median(lat) if lat else None, "p95": p95(lat), "max": max(lat, default=None)},
        "rechazos_falsos_(403_a_clientes_de_fondo)": codigos.get("403", 0),
        "criterio": {"p95_<=_300ms": bool(lat) and p95(lat) <= 300, "0_rechazos_falsos": codigos.get("403", 0) == 0},
    }
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    Path(args.jtl).with_name("resumen_jmeter.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False))


# ---------------- CLI ----------------


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def comunes(sp):
        sp.add_argument("--perfilamiento", default=os.getenv("PERF", "http://localhost:18002"))
        sp.add_argument("--consentimiento", default=os.getenv("CONS", "http://localhost:18005"))
        sp.add_argument("--secret", default=os.getenv("JWT_SECRET", "solventa-local"))
        sp.add_argument("--clientes", default=str(AQUI / "datos" / "clientes.json"))
        sp.add_argument("--insecure", action="store_true", help="no validar el certificado (autofirmado)")
        sp.add_argument("--ca", help="ruta al certificado autofirmado del ALB")

    sp = sub.add_parser("precargar")
    comunes(sp)
    sp.add_argument("--n", type=int, default=50, help="clientes de medicion")
    sp.add_argument("--n-fondo", type=int, default=50, help="clientes vigentes para la carga de JMeter")
    sp.set_defaults(f=precargar)

    sp = sub.add_parser("token")
    sp.add_argument("--secret", default=os.getenv("JWT_SECRET", "solventa-local"))
    sp.add_argument("--horas", type=float, default=8)
    sp.set_defaults(f=lambda a: print(token(a.secret, "jmeter-carga-fondo", "analista", "perfil:read", a.horas)))

    sp = sub.add_parser("medir")
    comunes(sp)
    sp.add_argument("--n", type=int, default=50)
    sp.add_argument("--escalonamiento", type=float, default=5, help="segundos entre el inicio de cada cliente")
    sp.add_argument("--sondeo", type=float, default=2, help="segundos entre consultas hasta el primer 403")
    sp.add_argument("--vigilancia", type=float, default=360, help="segundos de verificacion tras el primer 403")
    sp.add_argument("--sondeo-vigilancia", type=float, default=10)
    sp.add_argument("--mock", help="URL del mock de Open Finance para revisar su contador (opcional)")
    sp.add_argument("--salida", default=str(AQUI / "resultados"))
    sp.set_defaults(f=medir)

    sp = sub.add_parser("jmeter")
    sp.add_argument("jtl")
    sp.set_defaults(f=analizar_jmeter)

    args = p.parse_args()
    for attr in ("perfilamiento", "consentimiento", "mock"):
        if getattr(args, attr, None):
            setattr(args, attr, getattr(args, attr).rstrip("/"))
    args.f(args)


if __name__ == "__main__":
    main()
