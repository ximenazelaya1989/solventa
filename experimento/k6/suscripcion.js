/*
 * Experimento HU2.1.1 · Latencia de decisión + emisión (POST /suscripciones)
 *
 * Ejecutor "constant-arrival-rate": k6 inyecta exactamente TPS peticiones por
 * segundo, independientemente de cuánto tarde el servidor (modelo abierto).
 * Así la variable independiente es la carga ofrecida y no depende de la latencia.
 *
 * Uso:
 *   k6 run -e BASE_URL=http://<IP_PRIVADA_APP>:3000 -e TPS=50 -e DURACION=3m \
 *          -e NIVEL=operacion-normal -e REP=1 -e CSV=../seed/cotizaciones.csv \
 *          suscripcion.js
 */
import http from 'k6/http';
import { check } from 'k6';
import exec from 'k6/execution';
import { SharedArray } from 'k6/data';
import { Counter, Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const TPS = Number(__ENV.TPS || 50);
const DURACION = __ENV.DURACION || '3m';
const NIVEL = __ENV.NIVEL || 'sin-nombre';
const REP = __ENV.REP || '1';
const CSV = __ENV.CSV || '../seed/cotizaciones.csv';
const SALIDA = __ENV.SALIDA || 'resultados';

// Cada iteración usa una cotización distinta (cotizacionId es único en suscripciones).
const cotizaciones = new SharedArray('cotizaciones', () =>
  open(CSV)
    .trim()
    .split('\n')
    .slice(1)
    .map((linea) => {
      const [id, esperado] = linea.trim().split(',');
      return { id, esperado };
    }),
);

const decisiones = ['aprobada', 'revision', 'rechazada'];
// La API responde con los valores reales del enum Suscripcion.decision
// ('aprobado' | 'revision_asistida' | 'rechazado'), distintos de las
// etiquetas de `esperado` en el CSV (mismas que arriba). Se traduce solo
// para la comparación, sin tocar nombres de métricas/umbrales/CSV.
const CODIGO_A_ESPERADO = {
  aprobado: 'aprobada',
  revision_asistida: 'revision',
  rechazado: 'rechazada',
};
const latencia = {};
const suma = {};
const sumaCuadrados = {};
const muestras = {};
for (const d of [...decisiones, 'total']) {
  latencia[d] = new Trend(`latencia_${d}`, true);
  suma[d] = new Counter(`suma_ms_${d}`);
  sumaCuadrados[d] = new Counter(`suma_cuadrados_${d}`);
  muestras[d] = new Counter(`muestras_${d}`);
}
const errores = new Rate('tasa_error');
const decisionInesperada = new Counter('decision_inesperada');

export const options = {
  discardResponseBodies: false,
  scenarios: {
    suscripcion: {
      executor: 'constant-arrival-rate',
      rate: TPS,
      timeUnit: '1s',
      duration: DURACION,
      preAllocatedVUs: Math.max(10, TPS * 2),
      maxVUs: Math.max(50, TPS * 10),
    },
  },
  // Umbrales = medida del escenario de calidad HU2.1.1 (camino de aprobación automática).
  thresholds: {
    latencia_aprobada: ['p(95)<1500', 'p(99)<3000'],
    tasa_error: ['rate<0.01'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

function registrar(decision, ms) {
  latencia[decision].add(ms);
  suma[decision].add(ms);
  sumaCuadrados[decision].add(ms * ms);
  muestras[decision].add(1);
}

export default function () {
  const i = exec.scenario.iterationInTest;
  if (i >= cotizaciones.length) {
    exec.test.abort(`Dataset agotado en la iteración ${i}: aumente n en la semilla`);
  }
  const cotizacion = cotizaciones[i];
  const res = http.post(
    `${BASE_URL}/suscripciones`,
    JSON.stringify({ cotizacionId: cotizacion.id }),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'POST /suscripciones', esperado: cotizacion.esperado },
      timeout: '10s',
    },
  );

  const ok = check(res, {
    'status 201': (r) => r.status === 201,
    'no idempotente (petición nueva)': (r) => r.status === 201 && r.json('idempotente') === false,
  });
  errores.add(!ok);
  if (
    res.status === 201 &&
    CODIGO_A_ESPERADO[res.json('decision')] !== cotizacion.esperado
  )
    decisionInesperada.add(1);

  const ms = res.timings.duration;
  registrar('total', ms);
  if (res.status === 201) registrar(cotizacion.esperado, ms);
}

function desviacion(m, d) {
  const n = m[`muestras_${d}`] ? m[`muestras_${d}`].values.count : 0;
  if (n < 2) return null;
  const media = m[`suma_ms_${d}`].values.count / n;
  const varianza = m[`suma_cuadrados_${d}`].values.count / n - media * media;
  return Math.sqrt(Math.max(0, varianza));
}

function estadisticas(m, d) {
  const t = m[`latencia_${d}`];
  if (!t) return null;
  const v = t.values;
  return {
    muestras: m[`muestras_${d}`].values.count,
    p95: v['p(95)'],
    p99: v['p(99)'],
    promedio: v.avg,
    mediana: v.med,
    minimo: v.min,
    maximo: v.max,
    desviacion: desviacion(m, d),
  };
}

export function handleSummary(data) {
  const m = data.metrics;
  const aprob = estadisticas(m, 'aprobada');
  const resumen = {
    nivel: NIVEL,
    repeticion: Number(REP),
    tpsObjetivo: TPS,
    duracion: DURACION,
    throughput: m.http_reqs.values.rate,
    peticiones: m.http_reqs.values.count,
    tasaError: m.tasa_error ? m.tasa_error.values.rate : null,
    decisionesInesperadas: m.decision_inesperada ? m.decision_inesperada.values.count : 0,
    iteracionesDescartadas: m.dropped_iterations ? m.dropped_iterations.values.count : 0,
    vusMaximos: m.vus_max ? m.vus_max.values.max : null,
    latencia: {
      aprobada: aprob,
      revision: estadisticas(m, 'revision'),
      rechazada: estadisticas(m, 'rechazada'),
      total: estadisticas(m, 'total'),
    },
    cumpleASR: aprob ? aprob.p95 < 1500 && aprob.p99 < 3000 && (m.tasa_error ? m.tasa_error.values.rate : 0) < 0.01 : false,
  };
  const f = (x) => (x === null || x === undefined ? '-' : x.toFixed(1));
  const texto =
    `\n=== ${NIVEL} · rep ${REP} · ${TPS} TPS objetivo ===\n` +
    `throughput logrado: ${resumen.throughput.toFixed(2)} req/s · peticiones: ${resumen.peticiones}` +
    ` · error: ${((resumen.tasaError || 0) * 100).toFixed(2)} % · descartadas: ${resumen.iteracionesDescartadas}\n` +
    ['aprobada', 'revision', 'rechazada', 'total']
      .map((d) => {
        const e = resumen.latencia[d];
        return e
          ? `  ${d.padEnd(9)} n=${e.muestras} p95=${f(e.p95)} p99=${f(e.p99)} prom=${f(e.promedio)} ` +
              `min=${f(e.minimo)} max=${f(e.maximo)} desv=${f(e.desviacion)} ms`
          : `  ${d.padEnd(9)} sin muestras`;
      })
      .join('\n') +
    `\n  ASR HU2.1.1 (p95<1500 y p99<3000 en aprobadas, error<1 %): ${resumen.cumpleASR ? 'CUMPLE' : 'NO CUMPLE'}\n`;
  return {
    stdout: texto,
    [`${SALIDA}/${NIVEL}-rep${REP}.json`]: JSON.stringify(resumen, null, 2),
  };
}
