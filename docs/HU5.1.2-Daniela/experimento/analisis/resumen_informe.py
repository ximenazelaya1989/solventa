#!/usr/bin/env python3
"""Arma las tablas del informe de EXP-008 a partir de los resultados.

  python3 resumen_informe.py <carpeta_resultados>

Usa analizar.py para las corridas y agrega: las dos calibraciones, la corrida
piloto con C=20 y el resumen de CloudWatch en la ventana de medicion. Escribe
<carpeta>/analisis/datos_informe.json.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as a  # noqa: E402


def tabla_cal(ruta: Path) -> list[dict]:
    df = a.leer_jtl(ruta)
    filas = []
    for etiqueta, d in sorted(df.groupby('label')):
        lat = a.latencias_con_fallos(d)
        dur = max(1.0, d['t'].max() - d['t'].min())
        filas.append({'rps': int(etiqueta.split('_')[1]), 'n': len(d),
                      'ok_rps': round(d['ok'].sum() / dur, 1),
                      'p95': a.percentil(lat, 95), 'p99': a.percentil(lat, 99),
                      'error_pct': round(100 * (~d['ok']).mean(), 2)})
    return filas


def piloto(ruta: Path) -> dict:
    df = a.leer_jtl(ruta)
    v = df[(df['t'] >= 180) & (df['t'] < 480)]  # se detuvo en el minuto 8
    res = {}
    for s in 'ABC':
        lat = a.latencias_con_fallos(v[v['label'] == f'socio_{s}'])
        res[s] = {'p95': a.percentil(lat, 95), 'p99': a.percentil(lat, 99)}
    res['duracion_min'] = round(df['t'].max() / 60, 1)
    return res


def extra(ruta: Path) -> dict:
    """Linea base antes del pico (min 1 a 3) y desglose de errores en la ventana."""
    df = a.leer_jtl(ruta)
    abc = df[df['label'] != 'socio_D']
    base = abc[(abc['t'] >= 60) & (abc['t'] < 180)]
    ven = abc[(abc['t'] >= a.VENTANA[0]) & (abc['t'] < a.VENTANA[1])]
    lat_b = a.latencias_con_fallos(base)
    lat_v = a.latencias_con_fallos(ven)
    d = df[(df['label'] == 'socio_D') & (df['t'] >= a.PICO[0]) & (df['t'] < a.PICO[1])]
    resto = d[~d['ok']]
    return {
        'base_p95': a.percentil(lat_b, 95), 'base_p99': a.percentil(lat_b, 99),
        'ventana_p95': a.percentil(lat_v, 95), 'ventana_p99': a.percentil(lat_v, 99),
        'errores_abc': ven.loc[~ven['ok'], 'responseCode'].value_counts().to_dict(),
        'n_abc': len(ven),
        'd_resto': len(resto), 'd_429_pct_resto': round(100 * (resto['responseCode'] == '429').mean(), 3) if len(resto) else None,
        'd_otros': resto.loc[resto['responseCode'] != '429', 'responseCode'].value_counts().to_dict(),
    }


def cloudwatch(ruta: Path, inicio: str) -> dict:
    datos = json.loads(ruta.read_text())
    t0 = datetime.fromisoformat(inicio.replace('Z', '+00:00'))
    desde, hasta = t0 + timedelta(minutes=3), t0 + timedelta(minutes=10)
    out = {}
    for clave, serie in datos.items():
        vals = [v for ts, v in zip(serie['ts'], serie['valores'])
                if desde <= datetime.fromisoformat(ts) <= hasta]
        out[clave] = round(max(vals), 1) if vals else None
    return out


def fig_calibraciones(info: dict, ruta: Path):
    plt = a.plt
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    for nombre, color, etiqueta in (('calibracion', a.COLOR['B'], 'Calibración 1 (escalones de 20)'),
                                    ('calibracion_2', a.COLOR['A'], 'Calibración 2 (escalones de 10)')):
        if nombre not in info:
            continue
        t = pd.DataFrame(info[nombre])
        y = t['p95'].replace(np.inf, 10000)
        ax.plot(t['rps'], y, marker='o', ms=6, lw=2, color=color, label=etiqueta)
    ax.axhline(a.P95_MAX, color=a.TINTA2, lw=1, ls='--')
    ax.text(21, a.P95_MAX * 1.12, 'límite p95 = 250 ms', color=a.TINTA2, fontsize=8)
    ax.axvline(info['C'], color=a.TINTA2, lw=1, ls=':')
    ax.text(info['C'] + 1.5, 32, f"C = {info['C']:g}", color=a.TINTA, fontsize=9)
    ax.set_yscale('log')
    marcas = [25, 50, 100, 250, 500, 1000, 2500, 10000]
    ax.set_yticks(marcas, ['25', '50', '100', '250', '500', '1000', '2500', '≥10000'])
    ax.minorticks_off()
    ax.set_xlabel('carga ofrecida sin cuota (cotizaciones/s)')
    ax.set_ylabel('p95 del escalón (ms, log)')
    ax.legend(loc='lower right', fontsize=8)
    fig.tight_layout()
    fig.savefig(ruta, dpi=180)
    plt.close(fig)


def fig_resumen(info: dict, ruta: Path):
    plt = a.plt
    t = pd.DataFrame(info['socios'])
    def num(x):
        try:
            return float(x)
        except ValueError:
            return 10000.0
    fig, ejes = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
    for ax, col, lim, titulo in ((ejes[0], 'p95_ms', a.P95_MAX, 'p95 (límite 250 ms)'),
                                 (ejes[1], 'p99_ms', a.P99_MAX, 'p99 (límite 500 ms)')):
        for i, s in enumerate('ABC'):
            d = t[t['socio'] == s]
            ax.scatter(d['corrida'] + (i - 1) * 0.18, d[col].map(num), s=36, color=a.COLOR[s],
                       label=f'Socio {s}', zorder=3, edgecolors='#fcfcfb', linewidths=1)
        ax.axhline(lim, color=a.TINTA2, lw=1, ls='--')
        ax.set_yscale('log')
        ax.set_title(titulo, loc='left', fontsize=9, color=a.TINTA)
        etiquetas = [f"{n}\n{'con' if c == 'con' else 'sin'}" for n, c in
                     t[['corrida', 'cuota']].drop_duplicates().itertuples(index=False)]
        ax.set_xticks(sorted(t['corrida'].unique()), etiquetas)
        ax.set_xlabel('corrida y cuota')
    marcas = [10, 25, 50, 100, 250, 500, 1000, 2500, 10000]
    ejes[0].set_yticks(marcas, ['10', '25', '50', '100', '250', '500', '1000', '2500', '≥10000'])
    ejes[0].minorticks_off()
    ejes[0].set_ylabel('latencia en la ventana (ms, log)')
    ejes[1].legend(loc='upper right', fontsize=8)
    fig.tight_layout()
    fig.savefig(ruta, dpi=180)
    plt.close(fig)


def main(carpeta: Path):
    salida = carpeta / 'analisis'
    salida.mkdir(exist_ok=True)
    a.main(carpeta)  # tablas y figuras de las corridas + calibracion principal
    meta = json.loads((carpeta / 'corridas.json').read_text())
    info = {'C': meta['C'], 'cuota_rps': meta['cuota_rps']}
    crudos = carpeta / 'crudos'
    for nombre in ('calibracion', 'calibracion_2'):
        r = carpeta / f'{nombre}.jtl'
        if r.exists():
            info[nombre] = tabla_cal(r)
    p = carpeta / 'piloto_corrida_1_sin_C20.jtl'
    if p.exists():
        info['piloto'] = piloto(p)
    info['socios'] = pd.read_csv(salida / 'tabla_socios_normales.csv').to_dict('records')
    info['socio_d'] = pd.read_csv(salida / 'tabla_socio_d.csv').to_dict('records')
    info['veredicto'] = json.loads((salida / 'veredicto.json').read_text())
    info['cloudwatch'] = {}
    for c in meta['corridas']:
        nombre = c['jtl'][:-4]
        r = carpeta / f'cloudwatch_{nombre}.json'
        if r.exists():
            info['cloudwatch'][c['n']] = cloudwatch(r, c['inicio'])
    info['corridas'] = meta['corridas']
    info['extra'] = {c['n']: extra(carpeta / c['jtl']) for c in meta['corridas']}
    fig_calibraciones(info, salida / 'fig_calibraciones.png')
    fig_resumen(info, salida / 'fig_resumen.png')
    def limpio(x):
        # JSON valido: infinito como texto, NaN como null
        if isinstance(x, dict):
            return {str(k): limpio(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [limpio(v) for v in x]
        if isinstance(x, (float, np.floating)):
            return 'Infinity' if np.isinf(x) else (None if np.isnan(x) else float(x))
        if isinstance(x, (np.integer,)):
            return int(x)
        if isinstance(x, np.bool_):
            return bool(x)
        return x
    (salida / 'datos_informe.json').write_text(json.dumps(limpio(info), indent=1))
    print(json.dumps(info['veredicto']))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
