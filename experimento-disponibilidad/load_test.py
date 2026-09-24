#!/usr/bin/env python3
"""Prueba de carga del experimento H7.2.1 (disponibilidad del servicio de desembolso).

Que hace: simula N usuarios que envian pedidos POST /desembolsos. Si un pedido falla, el usuario lo
REINTENTA con el mismo siniestroId (por eso el servidor no puede duplicarlo). Mientras corre puedes
apretar ENTER para marcar un evento (por ejemplo, "detuve la instancia").

Ejemplos:
  python load_test.py --url http://localhost:8080 --nombre L01 --users 60 --ramp-up 5 --duration 60 --tps 10
  python load_test.py --url http://<DNS_ALB> --nombre B1 --users 60 --ramp-up 5 --duration 600 --tps 10
  python load_test.py --url http://localhost:3000 --modo idempotencia --nombre F03 --users 50
  python load_test.py --completar B1 --filas-bd 5990 --duplicados 0      (despues de contar en la BD)

Resultados (carpeta resultados/):  <nombre>/requests.csv, informe.html, resumen.json,
resumen_corridas.csv (una fila por corrida) y tabla.html (la tabla para tu analisis).
"""
import argparse
import asyncio
import csv
import html
import json
import os
import random
import sys
import threading
import time
import uuid
from datetime import datetime

try:
    import aiohttp
except ImportError:
    sys.exit('Falta la libreria aiohttp. Instalala con:  py -m pip install aiohttp')

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados')
MAESTRO = os.path.join(CARPETA, 'resumen_corridas.csv')
COLUMNAS = [
    'nombre', 'modo', 'descripcion', 'fecha', 'users', 'ramp_up_s', 'duracion_s', 'tps_objetivo', 'reintentos',
    'intentos_totales', 'error_pct', 'connect_prom_ms', 'connect_p95_ms', 'p90_ms', 'p95_ms', 'p99_ms',
    'throughput_rps', 'activos_max', 'activos_prom', 'unicas', 'exitos_1er_intento', 'exitos_tras_reintento',
    'fallos_finales', 'error_final_pct', 'disponibilidad_final_pct', 'seg_ultimo_error_tras_marca',
    'filas_bd', 'duplicados', 'perdidas',
]


# ----------------------------------------------------------------- utilidades
def percentil(valores, p):
    """Percentil por 'rango mas cercano': p99 = el valor bajo el cual queda el 99% de las peticiones."""
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    k = max(0, min(len(ordenados) - 1, int(round(p / 100 * len(ordenados))) - 1))
    return ordenados[k]


def promedio(valores):
    return sum(valores) / len(valores) if valores else 0.0


def hhmmss(epoch):
    return datetime.fromtimestamp(epoch).strftime('%H:%M:%S')


class Estado:
    def __init__(self):
        self.t0 = time.perf_counter()
        self.epoch0 = time.time()
        self.filas = []          # una por intento HTTP
        self.activos = 0         # usuarios activos ahora
        self.serie_activos = []  # (segundo, activos)
        self.marcas = []         # eventos marcados con ENTER
        self.terminado = False

    def seg(self):
        return time.perf_counter() - self.t0


class Ritmo:
    """Reparte los pedidos nuevos para que salgan a --tps por segundo (si no se pide, cada usuario va a su ritmo)."""

    def __init__(self, tps):
        self.intervalo = 1.0 / tps if tps else 0.0
        self.siguiente = 0.0

    async def esperar(self):
        if not self.intervalo:
            return
        ahora = time.perf_counter()
        turno = max(ahora, self.siguiente)
        self.siguiente = turno + self.intervalo
        if turno > ahora:
            await asyncio.sleep(turno - ahora)


# ----------------------------------------------------------------- una peticion
def crear_trace():
    """Mide el 'Connect Time': cuanto tarda en abrirse la conexion TCP con el servidor."""
    trace = aiohttp.TraceConfig()

    async def inicio(session, ctx, params):
        ctx.trace_request_ctx['t_conn'] = time.perf_counter()

    async def fin(session, ctx, params):
        d = ctx.trace_request_ctx
        d['connect_ms'] = (time.perf_counter() - d['t_conn']) * 1000

    trace.on_connection_create_start.append(inicio)
    trace.on_connection_create_end.append(fin)
    return trace


async def enviar(session, estado, url, cuerpo):
    ctx = {}
    activos = estado.activos
    seg_inicio = estado.seg()
    ts = time.time()
    inicio = time.perf_counter()
    status, error = 0, ''
    try:
        async with session.post(url, json=cuerpo, trace_request_ctx=ctx) as r:
            await r.read()
            status = r.status
            if status not in (200, 201):
                error = f'http_{status}'
    except asyncio.TimeoutError:
        error = 'timeout'
    except aiohttp.ClientConnectionError as e:
        error = 'conexion: ' + type(e).__name__
    except Exception as e:  # cualquier otro fallo tambien cuenta como error
        error = 'otro: ' + type(e).__name__
    latencia = (time.perf_counter() - inicio) * 1000
    if 'connect_ms' in ctx:
        conexion = ctx['connect_ms']
    elif 't_conn' in ctx:
        conexion = (time.perf_counter() - ctx['t_conn']) * 1000  # la conexion nunca se logro
    else:
        conexion = 0.0
    return dict(ts=ts, seg=seg_inicio, status=status, latencia_ms=latencia, connect_ms=conexion,
                error=error, ok=(error == ''), activos=activos)


# ----------------------------------------------------------------- usuarios
async def usuario_carga(i, args, estado, session, ritmo, fin):
    await asyncio.sleep(i * args.ramp_up / args.users)  # ramp-up: los usuarios entran de a poco
    estado.activos += 1
    try:
        while time.perf_counter() < fin:
            await ritmo.esperar()
            if time.perf_counter() >= fin:
                break
            sid = str(uuid.uuid4())
            cuerpo = {'siniestroId': sid, 'monto': random.randint(500, 9999)}
            for intento in range(1, args.reintentos + 1):
                fila = await enviar(session, estado, args.url.rstrip('/') + args.ruta, cuerpo)
                fila.update(id=sid, intento=intento)
                estado.filas.append(fila)
                if fila['ok']:
                    break
                if intento < args.reintentos:
                    await asyncio.sleep(args.espera_reintento)
    finally:
        estado.activos -= 1


async def usuario_idempotencia(args, estado, session, sid, barrera):
    estado.activos += 1
    try:
        await barrera.wait()  # todos salen exactamente a la vez
        fila = await enviar(session, estado, args.url.rstrip('/') + args.ruta, {'siniestroId': sid, 'monto': 1000})
        fila.update(id=sid, intento=1)
        estado.filas.append(fila)
    finally:
        estado.activos -= 1


# ----------------------------------------------------------------- monitor y marcas
async def monitor(estado, args):
    """Cada segundo: imprime una linea en vivo y guarda cuantos usuarios hay activos."""
    vistos = 0
    while not estado.terminado:
        await asyncio.sleep(1)
        s = int(estado.seg())
        estado.serie_activos.append((s, estado.activos))
        nuevas = estado.filas[vistos:]
        vistos = len(estado.filas)
        errores = sum(1 for f in nuevas if not f['ok'])
        p95 = percentil([f['latencia_ms'] for f in nuevas], 95)
        print(f't={s:>4}s  usuarios={estado.activos:>4}  intentos/s={len(nuevas):>4}  '
              f'errores/s={errores:>3}  p95={p95:>7.0f} ms', flush=True)


def escuchar_marcas(estado, loop):
    """ENTER = marca un evento. Puedes escribir un nombre antes de ENTER (ej. 'stop instancia')."""
    def leer():
        while not estado.terminado:
            try:
                texto = sys.stdin.readline()
            except Exception:
                return
            if texto == '':
                return
            texto = texto.strip() or f'marca {len(estado.marcas) + 1}'
            marca = dict(seg=estado.seg(), texto=texto, hora=hhmmss(time.time()))
            loop.call_soon_threadsafe(estado.marcas.append, marca)
            print(f'   >>> MARCA "{texto}" a los {marca["seg"]:.1f} s ({marca["hora"]})', flush=True)
    if sys.stdin and sys.stdin.isatty():
        threading.Thread(target=leer, daemon=True).start()
        print('Tip: aprieta ENTER (o escribe un nombre + ENTER) para marcar un evento, ej. "stop instancia".')


async def marcas_automaticas(estado, texto):
    """--marca-auto '10:stop instancia,20:reinicio' agrega marcas planeadas en esos segundos."""
    for item in texto.split(','):
        seg, _, nombre = item.partition(':')
        await asyncio.sleep(max(0, float(seg) - estado.seg()))
        marca = dict(seg=estado.seg(), texto=nombre.strip() or 'marca', hora=hhmmss(time.time()))
        estado.marcas.append(marca)
        print(f'   >>> MARCA "{marca["texto"]}" a los {marca["seg"]:.1f} s ({marca["hora"]})', flush=True)


# ----------------------------------------------------------------- resumen
def calcular(estado, args, nombre):
    filas = estado.filas
    duracion = max(max((f['seg'] + f['latencia_ms'] / 1000 for f in filas), default=1), 1)
    lat = [f['latencia_ms'] for f in filas]
    conx = [f['connect_ms'] for f in filas]
    activos = [a for _, a in estado.serie_activos] or [0]
    r = dict(
        nombre=nombre, descripcion=args.descripcion, fecha=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        users=args.users, ramp_up_s=args.ramp_up, duracion_s=args.duration if args.modo == 'carga' else '',
        tps_objetivo=args.tps or '', reintentos=args.reintentos if args.modo == 'carga' else 1,
        intentos_totales=len(filas),
        error_pct=round(100 * sum(1 for f in filas if not f['ok']) / len(filas), 3) if filas else 0,
        connect_prom_ms=round(promedio(conx), 2), connect_p95_ms=round(percentil(conx, 95), 2),
        p90_ms=round(percentil(lat, 90), 1), p95_ms=round(percentil(lat, 95), 1), p99_ms=round(percentil(lat, 99), 1),
        throughput_rps=round(len(filas) / duracion, 2), activos_max=max(activos), activos_prom=round(promedio(activos), 1),
    )
    por_id = {}
    for f in filas:
        por_id.setdefault(f['id'], []).append(f)
    e1 = e2 = ff = 0
    for intentos in por_id.values():
        intentos.sort(key=lambda x: x['intento'])
        if intentos[0]['ok']:
            e1 += 1
        elif any(x['ok'] for x in intentos):
            e2 += 1
        else:
            ff += 1
    u = len(por_id)
    r.update(unicas=u, exitos_1er_intento=e1, exitos_tras_reintento=e2, fallos_finales=ff,
             error_final_pct=round(100 * ff / u, 3) if u else 0,
             disponibilidad_final_pct=round(100 * (e1 + e2) / u, 4) if u else 0,
             seg_ultimo_error_tras_marca='', filas_bd='', duplicados='', perdidas='')
    r['modo'] = args.modo
    if args.modo == 'idempotencia':
        ok = sum(1 for f in filas if f['ok'])
        r.update(unicas=len(filas), exitos_1er_intento=ok, exitos_tras_reintento=0, fallos_finales=len(filas) - ok,
                 error_final_pct=r['error_pct'], disponibilidad_final_pct=round(100 * ok / len(filas), 4),
                 activos_max=args.users, activos_prom=args.users)
    fallidas = [f for f in filas if not f['ok']]
    if fallidas and estado.marcas:
        ultima = max(f['seg'] for f in fallidas)
        r['seg_ultimo_error_tras_marca'] = round(ultima - estado.marcas[0]['seg'], 1)
    return r


def imprimir(r, estado):
    print('\n' + '=' * 66)
    print(f' RESULTADO  {r["nombre"]}   {r["descripcion"]}')
    print('=' * 66)
    filas = [
        ('Tasa de error (% por intento)', f'{r["error_pct"]} %'),
        ('Connect time  promedio / p95', f'{r["connect_prom_ms"]} ms / {r["connect_p95_ms"]} ms'),
        ('Latencia  p90 / p95 / p99', f'{r["p90_ms"]} / {r["p95_ms"]} / {r["p99_ms"]} ms'),
        ('Throughput (intentos por segundo)', f'{r["throughput_rps"]}'),
        ('Hilos activos  max / promedio', f'{r["activos_max"]} / {r["activos_prom"]}'),
        ('-' * 34, '-' * 24),
        ('Intentos totales (con reintentos)', f'{r["intentos_totales"]}'),
        ('Pedidos unicos enviados', f'{r["unicas"]}'),
        ('Exitos 1er intento / tras reintento', f'{r["exitos_1er_intento"]} / {r["exitos_tras_reintento"]}'),
        ('Fallos finales (sin exito tras reintentos)', f'{r["fallos_finales"]}'),
        ('Disponibilidad final', f'{r["disponibilidad_final_pct"]} %'),
    ]
    for a, b in filas:
        print(f' {a:<44}{b}')
    for m in estado.marcas:
        print(f' Marca: "{m["texto"]}" a los {m["seg"]:.1f} s ({m["hora"]})')
    if r['seg_ultimo_error_tras_marca'] != '':
        print(f' Ultimo error: {r["seg_ultimo_error_tras_marca"]} s despues de la primera marca')
    print('=' * 66)
    if r.get('modo') == 'idempotencia':
        print(' Idempotencia: todas las peticiones llevan el MISMO siniestroId. En la BD debe haber 1 sola fila.')
    print(f' Falta contar en la BD:  SELECT count(*) FROM pagos;   y luego:')
    print(f'   python load_test.py --completar {r["nombre"]} --filas-bd <N> --duplicados 0')


# ----------------------------------------------------------------- HTML
def esc(x):
    return html.escape(str(x))


def grafico(titulo, series, marcas, unidad, xtotal=0, ancho=880, alto=250):
    """Grafico de lineas en SVG puro (sin librerias). series: [(nombre, color, [(x, y)])]"""
    pl, pr, pt, pb = 58, 14, 30, 34
    xs = [x for _, _, pts in series for x, _ in pts] or [0, 1]
    ys = [y for _, _, pts in series for _, y in pts] or [0, 1]
    xmax, ymax = max(max(xs), xtotal) or 1, (max(ys) or 1) * 1.1
    sx = lambda x: pl + (x / xmax) * (ancho - pl - pr)
    sy = lambda y: alto - pb - (y / ymax) * (alto - pt - pb)
    o = [f'<svg viewBox="0 0 {ancho} {alto}" class="graf" role="img" aria-label="{esc(titulo)}">',
         f'<text x="{pl}" y="18" class="gt">{esc(titulo)}</text>']
    for i in range(5):
        y = ymax * i / 4
        o.append(f'<line x1="{pl}" y1="{sy(y):.1f}" x2="{ancho - pr}" y2="{sy(y):.1f}" class="ejes"/>')
        o.append(f'<text x="{pl - 6}" y="{sy(y) + 4:.1f}" class="et" text-anchor="end">{y:.0f}</text>')
    for i in range(6):
        x = xmax * i / 5
        o.append(f'<text x="{sx(x):.1f}" y="{alto - 12}" class="et" text-anchor="middle">{x:.0f}s</text>')
    for m in marcas:
        if m['seg'] <= xmax:
            o.append(f'<line x1="{sx(m["seg"]):.1f}" y1="{pt}" x2="{sx(m["seg"]):.1f}" y2="{alto - pb}" class="marca"/>')
            o.append(f'<text x="{sx(m["seg"]) + 4:.1f}" y="{pt + 10}" class="mt">{esc(m["texto"])}</text>')
    for nombre, color, pts in series:
        if pts:
            d = ' '.join(f'{sx(x):.1f},{sy(y):.1f}' for x, y in pts)
            o.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.8"/>')
    leyenda = ''.join(f'<span><i style="background:{c}"></i>{esc(n)}</span>' for n, c, _ in series)
    o.append('</svg>')
    return f'<div class="gwrap">{"".join(o)}<div class="leyenda">{leyenda} <em>{esc(unidad)}</em></div></div>'


CSS = """
:root{--tinta:#12202b;--suave:#51677a;--linea:#dae3e9;--fondo:#f3f6f8;--tarjeta:#fff;--azul:#2e6690;--rojo:#b3402c;--verde:#2f7a54}
@media (prefers-color-scheme:dark){:root{--tinta:#e7eef3;--suave:#93a7b7;--linea:#28353f;--fondo:#0e161d;--tarjeta:#161f28;--azul:#7bb2dc;--rojo:#e28871;--verde:#7fc49c}}
*{box-sizing:border-box}body{margin:0;padding:24px 16px 60px;background:var(--fondo);color:var(--tinta);font:14px/1.5 'Segoe UI',Arial,sans-serif}
.p{max-width:1000px;margin:0 auto}h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:26px 0 8px}.sub{color:var(--suave);margin:0 0 16px}
.tarjetas{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.t{background:var(--tarjeta);border:1px solid var(--linea);border-radius:8px;padding:10px 12px}.t b{display:block;font-size:20px}.t span{color:var(--suave);font-size:12px}
table{border-collapse:collapse;width:100%;background:var(--tarjeta);border:1px solid var(--linea)}th,td{padding:6px 10px;border-bottom:1px solid var(--linea);text-align:right;white-space:nowrap}
th{background:var(--azul);color:#fff;font-size:12px}td:first-child,th:first-child,td:nth-child(2),th:nth-child(2){text-align:left}.scroll{overflow-x:auto}
.gwrap{background:var(--tarjeta);border:1px solid var(--linea);border-radius:8px;padding:8px;margin-bottom:12px}.graf{width:100%;height:auto}
.gt{font-weight:600;fill:var(--tinta);font-size:13px}.ejes{stroke:var(--linea)}.et{fill:var(--suave);font-size:10.5px}
.marca{stroke:var(--rojo);stroke-dasharray:5 4;stroke-width:1.5}.mt{fill:var(--rojo);font-size:11px}
.leyenda{display:flex;gap:16px;flex-wrap:wrap;color:var(--suave);font-size:12px;padding:2px 8px}.leyenda i{display:inline-block;width:12px;height:3px;margin-right:5px;vertical-align:middle}
.mal{color:var(--rojo);font-weight:600}.bien{color:var(--verde);font-weight:600}
"""


def por_segundo(estado):
    cubos = {}
    for f in estado.filas:
        c = cubos.setdefault(int(f['seg']), dict(n=0, err=0, lat=[]))
        c['n'] += 1
        c['err'] += 0 if f['ok'] else 1
        c['lat'].append(f['latencia_ms'])
    return cubos


def informe_html(r, estado, ruta):
    cubos = por_segundo(estado)
    segs = sorted(cubos)
    xtotal = max(max(segs, default=0), max((s for s, _ in estado.serie_activos), default=0))
    g1 = grafico('Latencia por segundo', [
        ('p95', '#2e6690', [(s, percentil(cubos[s]['lat'], 95)) for s in segs]),
        ('p99', '#b3402c', [(s, percentil(cubos[s]['lat'], 99)) for s in segs])], estado.marcas, 'milisegundos', xtotal)
    g2 = grafico('Throughput y errores por segundo', [
        ('intentos por segundo', '#2e6690', [(s, cubos[s]['n']) for s in segs]),
        ('errores por segundo', '#b3402c', [(s, cubos[s]['err']) for s in segs])], estado.marcas, 'peticiones', xtotal)
    g3 = grafico('Hilos (usuarios) activos', [
        ('activos', '#2f7a54', [(s, a) for s, a in estado.serie_activos])], estado.marcas, 'usuarios', xtotal)
    tarjetas = [
        (f'{r["error_pct"]} %', 'Tasa de error (por intento)'), (f'{r["connect_prom_ms"]} ms', 'Connect time promedio'),
        (f'{r["p90_ms"]} / {r["p95_ms"]} / {r["p99_ms"]} ms', 'Latencia p90 / p95 / p99'),
        (f'{r["throughput_rps"]}', 'Throughput (intentos/s)'), (f'{r["activos_max"]}', 'Hilos activos (max)'),
        (f'{r["disponibilidad_final_pct"]} %', 'Disponibilidad final (con reintentos)'),
    ]
    t = ''.join(f'<div class="t"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in tarjetas)
    marcas = ''.join(f'<li>«{esc(m["texto"])}» a los {m["seg"]:.1f} s ({m["hora"]})</li>' for m in estado.marcas) or '<li>Sin marcas</li>'
    pag = (f'<!doctype html><html lang="es"><meta charset="utf-8"><title>Informe {esc(r["nombre"])}</title>'
           f'<style>{CSS}</style><div class="p"><h1>Corrida {esc(r["nombre"])}</h1>'
           f'<p class="sub">{esc(r["descripcion"])} · {esc(r["fecha"])} · {r["users"]} usuarios · ramp-up {r["ramp_up_s"]} s · '
           f'tps objetivo {r["tps_objetivo"] or "libre"} · reintentos {r["reintentos"]}</p><div class="tarjetas">{t}</div>'
           f'<h2>Gráficas</h2>{g1}{g2}{g3}<h2>Marcas de eventos</h2><ul>{marcas}</ul>'
           f'<h2>Pedidos</h2><p>Únicos: {r["unicas"]} · éxitos al 1er intento: {r["exitos_1er_intento"]} · '
           f'éxitos tras reintento: {r["exitos_tras_reintento"]} · fallos finales: {r["fallos_finales"]}</p></div></html>')
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(pag)


def leer_maestro():
    if not os.path.exists(MAESTRO):
        return []
    with open(MAESTRO, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def guardar_maestro(filas):
    os.makedirs(CARPETA, exist_ok=True)
    with open(MAESTRO, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            w.writerow({c: fila.get(c, '') for c in COLUMNAS})


def tabla_html(filas):
    cols = [('nombre', 'Corrida'), ('descripcion', 'Descripción'), ('users', 'Users'), ('ramp_up_s', 'Ramp-up (s)'),
            ('duracion_s', 'Duración (s)'), ('tps_objetivo', 'TPS objetivo'),
            ('error_pct', 'Error %'), ('connect_prom_ms', 'Connect prom (ms)'), ('p90_ms', 'p90 (ms)'), ('p95_ms', 'p95 (ms)'),
            ('p99_ms', 'p99 (ms)'), ('throughput_rps', 'Throughput (req/s)'), ('activos_max', 'Hilos activos (max)'),
            ('activos_prom', 'Hilos activos (prom)'), ('unicas', 'Únicos'), ('exitos_tras_reintento', 'Éxitos tras reintento'),
            ('fallos_finales', 'Fallos finales'), ('disponibilidad_final_pct', 'Disponib. final %'),
            ('seg_ultimo_error_tras_marca', 'Seg. último error tras marca'), ('filas_bd', 'Filas BD'),
            ('perdidas', 'Pérdidas'), ('duplicados', 'Duplicados')]
    cab = ''.join(f'<th>{esc(t)}</th>' for _, t in cols)
    cuerpo = ''
    for f in filas:
        celdas = ''
        for k, _ in cols:
            v = f.get(k, '')
            cls = ''
            if k in ('perdidas', 'duplicados') and v != '':
                cls = ' class="bien"' if float(v) == 0 else ' class="mal"'
            celdas += f'<td{cls}>{esc(v)}</td>'
        cuerpo += f'<tr>{celdas}</tr>'
    pag = (f'<!doctype html><html lang="es"><meta charset="utf-8"><title>Tabla de corridas</title><style>{CSS}</style>'
           f'<div class="p" style="max-width:none"><h1>Tabla de corridas — H7.2.1</h1>'
           f'<p class="sub">Una fila por corrida. Las 5 primeras métricas son las del laboratorio: error %, connect time, percentiles, throughput e hilos activos.</p>'
           f'<div class="scroll"><table><tr>{cab}</tr>{cuerpo}</table></div></div></html>')
    with open(os.path.join(CARPETA, 'tabla.html'), 'w', encoding='utf-8') as f:
        f.write(pag)


# ----------------------------------------------------------------- flujo principal
async def correr(args):
    estado = Estado()
    conector = aiohttp.TCPConnector(limit=0, force_close=not args.keepalive)
    timeout = aiohttp.ClientTimeout(total=args.timeout, connect=args.timeout_conexion)
    async with aiohttp.ClientSession(connector=conector, timeout=timeout, trace_configs=[crear_trace()],
                                     headers={'Content-Type': 'application/json'}) as session:
        escuchar_marcas(estado, asyncio.get_running_loop())
        mon = asyncio.create_task(monitor(estado, args))
        if args.marca_auto:
            asyncio.create_task(marcas_automaticas(estado, args.marca_auto))
        if args.modo == 'idempotencia':
            sid = args.id or str(uuid.uuid4())
            barrera = asyncio.Event()
            tareas = [asyncio.create_task(usuario_idempotencia(args, estado, session, sid, barrera)) for _ in range(args.users)]
            await asyncio.sleep(0.5)
            barrera.set()
            await asyncio.gather(*tareas)
        else:
            ritmo = Ritmo(args.tps)
            fin = time.perf_counter() + args.duration
            tareas = [asyncio.create_task(usuario_carga(i, args, estado, session, ritmo, fin)) for i in range(args.users)]
            await asyncio.gather(*tareas)
        await asyncio.sleep(1.1)
        estado.terminado = True
        await mon
    return estado


def completar(args):
    filas = leer_maestro()
    fila = next((f for f in filas if f['nombre'] == args.completar), None)
    if not fila:
        sys.exit(f'No existe la corrida {args.completar}.')
    fila['filas_bd'] = args.filas_bd
    fila['duplicados'] = args.duplicados
    exitos = int(fila['exitos_1er_intento']) + int(fila['exitos_tras_reintento'])
    if fila.get('modo') == 'idempotencia':
        fila['duplicados'] = max(0, args.filas_bd - 1)
        fila['perdidas'] = 0 if args.filas_bd >= 1 else 1
        print(f'{args.completar}: {exitos} respuestas exitosas, filas en BD={args.filas_bd} (esperado 1) -> duplicados={fila["duplicados"]}')
    else:
        fila['perdidas'] = max(0, exitos - args.filas_bd)
        print(f'{args.completar}: exitos confirmados={exitos}, filas en BD={args.filas_bd} -> perdidas={fila["perdidas"]}, duplicados={args.duplicados}')
    guardar_maestro(filas)
    tabla_html(filas)
    print(f'Tabla actualizada: {os.path.join(CARPETA, "tabla.html")}')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--url', default='http://localhost:8080', help='base del servicio (DNS del ALB o localhost)')
    p.add_argument('--ruta', default='/desembolsos')
    p.add_argument('--nombre', default=datetime.now().strftime('corrida_%H%M%S'), help='id de la corrida (ej. B1)')
    p.add_argument('--descripcion', default='', help='texto libre (ej. "3 instancias, stop en min 3")')
    p.add_argument('--modo', choices=['carga', 'idempotencia'], default='carga')
    p.add_argument('--users', type=int, default=60, help='usuarios simultaneos (hilos)')
    p.add_argument('--ramp-up', dest='ramp_up', type=float, default=5, help='segundos para que entren todos los usuarios')
    p.add_argument('--duration', type=float, default=60, help='segundos de la prueba')
    p.add_argument('--tps', type=float, default=0, help='pedidos nuevos por segundo (0 = cada usuario va a su ritmo)')
    p.add_argument('--reintentos', type=int, default=3, help='intentos maximos por pedido (mismo siniestroId)')
    p.add_argument('--espera-reintento', dest='espera_reintento', type=float, default=1.0)
    p.add_argument('--timeout', type=float, default=5.0)
    p.add_argument('--timeout-conexion', dest='timeout_conexion', type=float, default=3.0)
    p.add_argument('--keepalive', action='store_true', help='reusar conexiones (por defecto abre una nueva por peticion)')
    p.add_argument('--id', help='siniestroId fijo (solo modo idempotencia)')
    p.add_argument('--marca-auto', dest='marca_auto', help="marcas planeadas, ej. '180:stop instancia,360:reinicio'")
    p.add_argument('--completar', metavar='NOMBRE', help='agrega filas_bd y duplicados a una corrida ya hecha')
    p.add_argument('--filas-bd', dest='filas_bd', type=int)
    p.add_argument('--duplicados', type=int, default=0)
    args = p.parse_args()

    if args.completar:
        if args.filas_bd is None:
            sys.exit('Con --completar tambien necesitas --filas-bd N')
        return completar(args)

    print(f'Corrida {args.nombre}: {args.modo}, {args.users} usuarios, ramp-up {args.ramp_up}s, '
          f'duracion {args.duration}s, tps {args.tps or "libre"}, destino {args.url}{args.ruta}\n')
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    estado = asyncio.run(correr(args))
    if not estado.filas:
        sys.exit('No se registro ninguna peticion.')

    r = calcular(estado, args, args.nombre)
    imprimir(r, estado)

    carpeta_run = os.path.join(CARPETA, args.nombre)
    os.makedirs(carpeta_run, exist_ok=True)
    with open(os.path.join(carpeta_run, 'requests.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['timestamp_iso', 'metodo', 'endpoint', 'status_code', 'latency_ms', 'connect_ms', 'error',
                    'siniestro_id', 'intento', 'hilos_activos'])
        for x in estado.filas:
            w.writerow([datetime.fromtimestamp(x['ts']).isoformat(timespec='milliseconds'), 'POST', args.ruta,
                        x['status'], round(x['latencia_ms'], 1), round(x['connect_ms'], 1), x['error'],
                        x['id'], x['intento'], x['activos']])
    with open(os.path.join(carpeta_run, 'resumen.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(resumen=r, marcas=estado.marcas), f, indent=2, ensure_ascii=False)
    informe_html(r, estado, os.path.join(carpeta_run, 'informe.html'))

    filas = [f for f in leer_maestro() if f['nombre'] != args.nombre] + [r]
    guardar_maestro(filas)
    tabla_html(filas)
    print(f'\nInforme con gráficas : {os.path.join(carpeta_run, "informe.html")}')
    print(f'Tabla de todas las corridas: {os.path.join(CARPETA, "tabla.html")}')


if __name__ == '__main__':
    main()
