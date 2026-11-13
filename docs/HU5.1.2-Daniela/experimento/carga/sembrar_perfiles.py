#!/usr/bin/env python3
"""Siembra los 10.000 perfiles de riesgo del experimento usando POST /perfiles
de Perfilamiento (el contrato existente, sin tocar su BD a mano).

  python3 sembrar_perfiles.py http://<alb-interno>:8002 [cantidad]

Los ids son 00000000-0000-4000-8000-1000000xxxxx (1..cantidad), los mismos que
usa el plan de JMeter. Un 409 significa que el perfil ya existia.
"""
import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = sys.argv[1].rstrip('/')
CANTIDAD = int(sys.argv[2]) if len(sys.argv) > 2 else 10_000


def crear(i: int) -> int:
    cliente = f'00000000-0000-4000-8000-{100000000000 + i:012d}'
    cuerpo = json.dumps({'clienteId': cliente, 'score': 20 + (i * 37) % 76}).encode()
    pet = urllib.request.Request(f'{URL}/perfiles', data=cuerpo, method='POST',
                                 headers={'content-type': 'application/json'})
    try:
        with urllib.request.urlopen(pet, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


with ThreadPoolExecutor(max_workers=16) as ex:
    codigos = list(ex.map(crear, range(1, CANTIDAD + 1)))
resumen = {c: codigos.count(c) for c in sorted(set(codigos))}
print(json.dumps({'perfiles': CANTIDAD, 'codigos': resumen}))
sys.exit(0 if set(resumen) <= {201, 409} else 1)
