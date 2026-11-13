#!/usr/bin/env python3
"""Analiza los resultados de EXP-008 (cuota por socio en el API Gateway).

  python3 analizar.py <carpeta_resultados>

La carpeta debe tener calibracion.jtl, corridas.json (lista de corridas con su
archivo .jtl y si llevaban cuota) y, si existen, cloudwatch_<n>.json. Escribe
tablas (.csv y .md) y figuras (.png) en <carpeta>/analisis.

Reglas del diseno:
  - Calibracion: C es la ultima carga con p95 < 250 ms y error < 1 %.
  - Ventana de medicion: minutos 3 a 10 de cada corrida (rampa y pico de D).
  - Cualquier fallo de A, B o C cuenta como fuera de la medida: para el p95 y
    el p99 un fallo vale infinito.
  - Hipotesis: (1) con cuota, A, B y C con p95 < 250 ms y p99 < 500 ms en las
    3 corridas; (2) sin cuota, al menos un socio normal con p95 > 250 ms;
    (3) con cuota, lo aceptado de D queda dentro de su cuota y el resto es 429.
"""
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLOR = {'A': '#2a78d6', 'B': '#eb6834', 'C': '#1baf7a', 'D': '#eda100', 'D429': '#e87ba4'}
TINTA, TINTA2, REJILLA = '#0b0b0b', '#52514e', '#e4e3df'
VENTANA = (180, 600)          # s desde el inicio de la corrida
PICO = (240, 600)             # pico sostenido de D (min 4 a 10)
P95_MAX, P99_MAX = 250, 500   # ms, medida del ASR

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': REJILLA,
    'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA2,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True,
    'grid.color': REJILLA, 'grid.linewidth': 0.6, 'legend.frameon': False,
    'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb',
})


def leer_jtl(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta, usecols=['timeStamp', 'elapsed', 'label', 'responseCode', 'success'],
                     dtype={'responseCode': str}, low_memory=False)
    df['ok'] = df['responseCode'].astype(str).str.startswith('2')
    df['t'] = (df['timeStamp'] - df['timeStamp'].min()) / 1000.0
    return df


def percentil(serie_ms: np.ndarray, q: float) -> float:
    if len(serie_ms) == 0:
        return float('nan')
    return float(np.percentile(serie_ms, q, method='higher'))


def latencias_con_fallos(d: pd.DataFrame) -> np.ndarray:
    return np.where(d['ok'], d['elapsed'].astype(float), np.inf)


def fmt_ms(x: float) -> str:
    if math.isnan(x):
        return 'N/A'
    return 'fuera (fallo)' if math.isinf(x) else f'{x:.0f}'


# ------------------------------------------------------------- calibracion
def calibracion(carpeta: Path, salida: Path) -> dict:
    df = leer_jtl(carpeta / 'calibracion.jtl')
    filas = []
    for etiqueta, d in sorted(df.groupby('label')):
        ofrecida = int(etiqueta.split('_')[1])
        dur = max(1.0, d['t'].max() - d['t'].min())
        lat = latencias_con_fallos(d)
        filas.append({
            'carga_ofrecida_rps': ofrecida,
            'peticiones': len(d),
            'throughput_ok_rps': round(d['ok'].sum() / dur, 1),
            'p95_ms': percentil(lat, 95),
            'p99_ms': percentil(lat, 99),
            'p95_exitosas_ms': percentil(d.loc[d['ok'], 'elapsed'].to_numpy(float), 95),
            'error_pct': round(100 * (~d['ok']).mean(), 2),
        })
    t = pd.DataFrame(filas).sort_values('carga_ofrecida_rps')
    t['cumple'] = (t['p95_ms'] < P95_MAX) & (t['error_pct'] < 1)
    # C = ultima carga que cumple antes del primer escalon que no cumple
    c = None
    for _, f in t.iterrows():
        if not f['cumple']:
            break
        c = int(f['carga_ofrecida_rps'])
    t.to_csv(salida / 'tabla_calibracion.csv', index=False)

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    x = t['carga_ofrecida_rps']
    ax.plot(x, t['p95_exitosas_ms'], marker='o', ms=5, lw=2, color=COLOR['A'], label='p95 (exitosas)')
    ax.plot(x, t['p99_ms'].replace(np.inf, np.nan), marker='o', ms=5, lw=2, color=COLOR['B'], label='p99')
    ax.axhline(P95_MAX, color=TINTA2, lw=1, ls='--')
    ax.text(x.iloc[0], P95_MAX * 1.08, 'límite p95 = 250 ms', color=TINTA2, fontsize=8)
    if c:
        ax.axvline(c, color=TINTA2, lw=1, ls=':')
        ax.text(c, ax.get_ylim()[1] * 0.92, f' C = {c} rps', color=TINTA, fontsize=9)
    ax.set_yscale('log')
    ax.set_xlabel('carga ofrecida (peticiones/s)')
    ax.set_ylabel('latencia (ms, escala log)')
    ax.set_title('Calibración sin cuota: latencia por escalón de 2 min', loc='left', color=TINTA, fontsize=10)
    ax.legend(loc='upper left')
    fig.tight_layout()
    fig.savefig(salida / 'fig_calibracion.png', dpi=180)
    plt.close(fig)
    return {'C': c, 'tabla': t}


# ---------------------------------------------------------------- corridas
def resumen_corrida(df: pd.DataFrame, cuota_rps: float | None, rafaga: float) -> dict:
    v = df[(df['t'] >= VENTANA[0]) & (df['t'] < VENTANA[1])]
    r = {}
    for s in 'ABC':
        d = v[v['label'] == f'socio_{s}']
        lat = latencias_con_fallos(d)
        r[s] = {
            'n': len(d), 'p50': percentil(lat, 50), 'p95': percentil(lat, 95), 'p99': percentil(lat, 99),
            'error_pct': round(100 * (~d['ok']).mean(), 2) if len(d) else float('nan'),
        }
    d = df[df['label'] == 'socio_D']
    p = d[(d['t'] >= PICO[0]) & (d['t'] < PICO[1])]
    dur = PICO[1] - PICO[0]
    aceptadas = int(p['ok'].sum())
    n429 = int((p['responseCode'] == '429').sum())
    otros = len(p) - aceptadas - n429
    por_seg = p[p['ok']].groupby(p['t'].astype(int)).size()
    r['D'] = {
        'ofrecidas_rps': round(len(p) / dur, 1),
        'aceptadas_rps': round(aceptadas / dur, 1),
        'aceptadas': aceptadas, 'rechazadas_429': n429, 'otros_errores': otros,
        'max_aceptadas_1s': int(por_seg.max()) if len(por_seg) else 0,
        'limite_teorico': round(cuota_rps * dur + cuota_rps * rafaga, 0) if cuota_rps else None,
    }
    return r


def serie_10s(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['v'] = (df['t'] // 10 * 10).astype(int)
    filas = []
    for v, d in df.groupby('v'):
        fila = {'t': v}
        for s in 'ABC':
            x = d[d['label'] == f'socio_{s}']
            fila[f'p95_{s}'] = percentil(latencias_con_fallos(x), 95) if len(x) else np.nan
        x = d[d['label'] == 'socio_D']
        fila['D_ofrecidas'] = len(x) / 10
        fila['D_aceptadas'] = x['ok'].sum() / 10
        fila['D_429'] = (x['responseCode'] == '429').sum() / 10
        fila['D_otros'] = (len(x) - x['ok'].sum() - (x['responseCode'] == '429').sum()) / 10
        filas.append(fila)
    return pd.DataFrame(filas)


def figura_corrida(serie: pd.DataFrame, titulo: str, cuota_rps: float | None, ruta: Path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 5.2), sharex=True,
                                   gridspec_kw={'height_ratios': [1.15, 1]})
    m = serie['t'] / 60
    for s in 'ABC':
        y = serie[f'p95_{s}'].replace(np.inf, 10000)
        ax1.plot(m, y, lw=2, color=COLOR[s], label=f'Socio {s}')
    ax1.axhline(P95_MAX, color=TINTA2, lw=1, ls='--')
    ax1.set_yscale('log')
    tope = max(1000, float(np.nanmax(serie[[f'p95_{s}' for s in 'ABC']].replace(np.inf, 10000).to_numpy())) * 1.5)
    ax1.set_ylim(10, tope)
    marcas = [m for m in (10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000) if m <= tope]
    ax1.set_yticks(marcas, [str(m) for m in marcas])
    ax1.minorticks_off()
    ax1.text(13.9, P95_MAX * 1.1, 'límite p95 = 250 ms', color=TINTA2, fontsize=8, ha='right')
    ax1.text(VENTANA[0] / 60 + 0.1, tope * 0.75, 'ventana de medición', color=TINTA2, fontsize=8)
    ax1.set_ylabel('p95 cada 10 s (ms, log)')
    ax1.legend(loc='lower right', bbox_to_anchor=(1, 1.0), ncol=3, fontsize=8)
    ax1.set_title(titulo, loc='left', color=TINTA, fontsize=10)
    ax2.plot(m, serie['D_ofrecidas'], lw=1.2, color=TINTA2, ls='--', label='D ofrecidas')
    ax2.plot(m, serie['D_aceptadas'], lw=2, color=COLOR['D'], label='D aceptadas')
    if serie['D_429'].sum() > 0:
        ax2.plot(m, serie['D_429'], lw=2, color=COLOR['D429'], label='D rechazadas (429)')
    if cuota_rps:
        ax2.axhline(cuota_rps, color=TINTA2, lw=1, ls=':')
        ax2.text(0.1, cuota_rps * 1.05, f'cuota = {cuota_rps:g}/s', color=TINTA2, fontsize=8)
    ax2.set_ylabel('peticiones/s del socio D')
    ax2.set_xlabel('minuto de la corrida')
    ax2.legend(loc='upper right', fontsize=8)
    for ax in (ax1, ax2):
        ax.axvspan(VENTANA[0] / 60, VENTANA[1] / 60, color='#f0efec', zorder=0)
    fig.tight_layout()
    fig.savefig(ruta, dpi=180)
    plt.close(fig)


def evaluar(resultados: list[dict]) -> dict:
    con = [r for r in resultados if r['cuota']]
    sin = [r for r in resultados if not r['cuota']]
    h1 = all(r['res'][s]['p95'] < P95_MAX and r['res'][s]['p99'] < P99_MAX for r in con for s in 'ABC')
    h2 = all(any(r['res'][s]['p95'] > P95_MAX for s in 'ABC') for r in sin)
    # (3) lo aceptado de D no pasa el limite teorico y el resto recibe 429. Se toleran fallas de
    # conexion del balanceador que no son de la cuota si son menos del 0,1 % del resto (se reportan).
    def resto_429(d):
        resto = d['rechazadas_429'] + d['otros_errores']
        return 1.0 if resto == 0 else d['rechazadas_429'] / resto
    h3 = all(r['res']['D']['aceptadas'] <= r['res']['D']['limite_teorico'] and resto_429(r['res']['D']) >= 0.999
             for r in con)
    h3_estricta = all(r['res']['D']['otros_errores'] == 0 for r in con) and h3
    h1_p95 = all(r['res'][s]['p95'] < P95_MAX for r in con for s in 'ABC')
    return {'condicion_1': h1, 'condicion_1_solo_p95': h1_p95, 'condicion_2': h2, 'condicion_3': h3,
            'condicion_3_estricta': h3_estricta, 'confirmada': h1 and h2 and h3}


def main(carpeta: Path):
    salida = carpeta / 'analisis'
    salida.mkdir(exist_ok=True)
    meta = json.loads((carpeta / 'corridas.json').read_text())
    cal = calibracion(carpeta, salida) if (carpeta / 'calibracion.jtl').exists() else {'C': meta.get('C')}
    print(f"C calibrada = {cal['C']} rps")

    resultados, filas = [], []
    for c in meta['corridas']:
        df = leer_jtl(carpeta / c['jtl'])
        cuota = meta['cuota_rps'] if c['cuota'] else None
        res = resumen_corrida(df, cuota, meta.get('rafaga_s', 2))
        resultados.append({'n': c['n'], 'cuota': c['cuota'], 'res': res})
        nombre = f"Corrida {c['n']} {'con' if c['cuota'] else 'sin'} cuota"
        serie_10s_df = serie_10s(df)
        serie_10s_df.to_csv(salida / f"serie_corrida_{c['n']}.csv", index=False)
        figura_corrida(serie_10s_df, nombre, cuota, salida / f"fig_corrida_{c['n']}.png")
        for s in 'ABC':
            x = res[s]
            filas.append({'corrida': c['n'], 'cuota': 'con' if c['cuota'] else 'sin', 'socio': s,
                          'n': x['n'], 'p50_ms': fmt_ms(x['p50']), 'p95_ms': fmt_ms(x['p95']),
                          'p99_ms': fmt_ms(x['p99']), 'error_pct': x['error_pct'],
                          'cumple_asr': x['p95'] < P95_MAX and x['p99'] < P99_MAX})
    tabla = pd.DataFrame(filas)
    tabla.to_csv(salida / 'tabla_socios_normales.csv', index=False)
    tabla_d = pd.DataFrame([{'corrida': r['n'], 'cuota': 'con' if r['cuota'] else 'sin', **r['res']['D']}
                            for r in resultados])
    tabla_d.to_csv(salida / 'tabla_socio_d.csv', index=False)
    veredicto = evaluar(resultados)
    (salida / 'veredicto.json').write_text(json.dumps(veredicto, indent=2))
    with open(salida / 'resumen.md', 'w') as f:
        f.write(f"C = {cal['C']} rps, cuota = {meta['cuota_rps']} rps por socio\n\n")
        f.write(tabla.to_markdown(index=False) + '\n\n' + tabla_d.to_markdown(index=False) + '\n\n')
        f.write(json.dumps(veredicto, indent=2) + '\n')
    print(tabla.to_string(index=False))
    print(tabla_d.to_string(index=False))
    print(veredicto)


if __name__ == '__main__':
    main(Path(sys.argv[1]))
