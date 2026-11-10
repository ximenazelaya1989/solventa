// EXP-006 (H7.2.1) - Carga de desembolsos con k6.
// 10.000 ordenes a tasa constante de 10 por segundo (unos 17 minutos).
// Cada orden aprueba un siniestro y pide el pago de su indemnizacion.
// La disponibilidad es ordenes completadas (201) / ordenes enviadas.
//
//   k6 run -e SINIESTROS_URL=http://<alb> carga.js
//   k6 run -e SINIESTROS_URL=http://<alb> -e TPS=1 -e DURACION=60s carga.js   # smoke test
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const TPS = Number(__ENV.TPS || 10);
const DURACION = __ENV.DURACION || '1000s';

export const options = {
  scenarios: {
    desembolsos: {
      executor: 'constant-arrival-rate',
      rate: TPS,
      timeUnit: '1s',
      duration: DURACION,
      preAllocatedVUs: 50,
      // Una orden afectada por la falla puede tardar hasta ~30 s reintentando:
      // a 10 TPS se necesitan cientos de VUs en vuelo para no perder ordenes.
      maxVUs: 600,
    },
  },
  // Criterio del ASR: disponibilidad >= 99,99 %
  thresholds: { checks: ['rate>=0.9999'] },
  summaryTrendStats: ['avg', 'min', 'med', 'p(95)', 'p(99)', 'max'],
};

const completadas = new Counter('ordenes_completadas');
const fallidas = new Counter('ordenes_fallidas');

export default function () {
  const res = http.post(
    `${__ENV.SINIESTROS_URL}/siniestros/indemnizaciones`,
    JSON.stringify({ monto: 1000, moneda: 'USD' }),
    {
      headers: { 'content-type': 'application/json' },
      // Mayor que el presupuesto de reintentos de Siniestros (30 s): si no,
      // k6 contaria como fallida una orden que si se completo.
      timeout: '60s',
      tags: { name: 'indemnizacion' },
    },
  );
  const ok = check(res, { 'pago confirmado (201)': (r) => r.status === 201 });
  if (ok) completadas.add(1);
  else fallidas.add(1);
}
