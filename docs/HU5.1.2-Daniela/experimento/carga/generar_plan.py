#!/usr/bin/env python3
"""Genera los planes de JMeter 5.6.3 de EXP-008 (Open Model Thread Group).

  corrida      Cuatro socios. A, B y C envian 0,15C constante durante 14 min. D
               se queda en 0,15C 3 min, sube en 1 min a 1,5C (10x), sostiene el
               pico 6 min, baja en 1 min y se recupera 3 min.
  calibracion  Carga escalonada sin cuota: +PASO peticiones/s cada 2 min.
  humo         Prueba corta de 1 min para revisar el montaje.

El host y el puerto se pasan al correr: jmeter -n -t plan.jmx -Jhost=... -Jport=80

  python3 generar_plan.py corrida --c 100 --salida corrida.jmx
  python3 generar_plan.py calibracion --desde 20 --paso 20 --hasta 200 --salida calibracion.jmx
"""
import argparse
from xml.sax.saxutils import escape

PRODUCTO = '22222222-2222-2222-2222-222222222222'
# Los 10.000 clientes sembrados tienen ids 00000000-0000-4000-8000-1000000xxxxx.
CUERPO = ('{"clienteId":"00000000-0000-4000-8000-${__Random(100000000001,100000010000)}",'
          f'"productoId":"{PRODUCTO}"}}')
CLAVES = {'A': 'exp008-socio-a', 'B': 'exp008-socio-b', 'C': 'exp008-socio-c', 'D': 'exp008-socio-d'}


def por_minuto(rps: float) -> int:
    return max(1, round(rps * 60))


def grupo(nombre: str, etiqueta: str, clave: str, programa: str) -> str:
    return f'''
      <OpenModelThreadGroup guiclass="OpenModelThreadGroupGui" testclass="OpenModelThreadGroup" testname="{escape(nombre)}">
        <elementProp name="ThreadGroup.main_controller" elementType="OpenModelThreadGroupController"/>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <stringProp name="OpenModelThreadGroup.schedule">{escape(programa)}</stringProp>
        <stringProp name="OpenModelThreadGroup.random_seed"></stringProp>
      </OpenModelThreadGroup>
      <hashTree>
        <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="Encabezados">
          <collectionProp name="HeaderManager.headers">
            <elementProp name="" elementType="Header">
              <stringProp name="Header.name">Content-Type</stringProp>
              <stringProp name="Header.value">application/json</stringProp>
            </elementProp>
            <elementProp name="" elementType="Header">
              <stringProp name="Header.name">x-api-key</stringProp>
              <stringProp name="Header.value">{escape(clave)}</stringProp>
            </elementProp>
          </collectionProp>
        </HeaderManager>
        <hashTree/>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{escape(etiqueta)}">
          <stringProp name="HTTPSampler.domain">${{__P(host)}}</stringProp>
          <stringProp name="HTTPSampler.port">${{__P(port,80)}}</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.path">/v1/cotizaciones</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <boolProp name="HTTPArgument.always_encode">false</boolProp>
                <stringProp name="Argument.value">{escape(CUERPO)}</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
          <stringProp name="HTTPSampler.connect_timeout">2000</stringProp>
          <stringProp name="HTTPSampler.response_timeout">10000</stringProp>
          <stringProp name="HTTPSampler.implementation">HttpClient4</stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>'''


def plan(nombre: str, grupos: list[str]) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{escape(nombre)}">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="Variables">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
    </TestPlan>
    <hashTree>{''.join(grupos)}
    </hashTree>
  </hashTree>
</jmeterTestPlan>
'''


def corrida(c: float) -> str:
    base, pico = por_minuto(0.15 * c), por_minuto(1.5 * c)
    normal = f'rate({base}/min) random_arrivals(14 min) rate({base}/min)'
    socio_d = (f'rate({base}/min) random_arrivals(3 min) rate({base}/min) random_arrivals(1 min) '
               f'rate({pico}/min) random_arrivals(6 min) rate({pico}/min) random_arrivals(1 min) '
               f'rate({base}/min) random_arrivals(3 min) rate({base}/min)')
    grupos = [grupo(f'Socio {s}', f'socio_{s}', CLAVES[s], normal) for s in 'ABC']
    grupos.append(grupo('Socio D (pico 10x)', 'socio_D', CLAVES['D'], socio_d))
    return plan(f'EXP-008 corrida C={c:g}', grupos)


def calibracion(desde: int, paso: int, hasta: int) -> str:
    grupos = []
    for i, rps in enumerate(range(desde, hasta + 1, paso)):
        espera = f'pause({2 * i} min) ' if i else ''
        programa = f'{espera}rate({por_minuto(rps)}/min) random_arrivals(2 min) rate({por_minuto(rps)}/min)'
        grupos.append(grupo(f'Escalon {rps} rps', f'cal_{rps:03d}', 'exp008-calibracion', programa))
    return plan(f'EXP-008 calibracion {desde}-{hasta} rps', grupos)


def humo(rps: float) -> str:
    programa = f'rate({por_minuto(rps)}/min) random_arrivals(1 min) rate({por_minuto(rps)}/min)'
    return plan('EXP-008 humo', [grupo(f'Socio {s}', f'socio_{s}', CLAVES[s], programa) for s in 'ABCD'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('tipo', choices=['corrida', 'calibracion', 'humo'])
    p.add_argument('--c', type=float, help='capacidad calibrada C en peticiones/s')
    p.add_argument('--desde', type=int, default=20)
    p.add_argument('--paso', type=int, default=20)
    p.add_argument('--hasta', type=int, default=200)
    p.add_argument('--rps', type=float, default=5)
    p.add_argument('--salida', required=True)
    a = p.parse_args()
    if a.tipo == 'corrida':
        texto = corrida(a.c)
    elif a.tipo == 'calibracion':
        texto = calibracion(a.desde, a.paso, a.hasta)
    else:
        texto = humo(a.rps)
    with open(a.salida, 'w', encoding='utf-8') as f:
        f.write(texto)
    print(f'Plan escrito en {a.salida}')
