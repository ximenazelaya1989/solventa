import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// Ajusta antes de correr:
//   BASE_URL=http://TU-ALB-DNS PRODUCTO_ID=uuid-real DURACION=5m k6 run carga-cotizaciones.js
const BASE_URL = __ENV.BASE_URL || 'http://CAMBIA-ESTO.us-east-1.elb.amazonaws.com';
const PRODUCTO_ID = __ENV.PRODUCTO_ID || 'CAMBIA-ESTO-por-un-producto-id-real';

export const options = {
  scenarios: {
    trafico_constante: {
      executor: 'constant-vus',
      vus: 20,
      duration: __ENV.DURACION || '5m',
    },
  },
  thresholds: {
    // Si el error rate sube de 1% durante la ventana del rolling update,
    // significa que SI hubo downtime perceptible por el cliente.
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1500'],
  },
};

export default function () {
  const nivelRiesgo = ['bajo', 'medio', 'alto'][Math.floor(Math.random() * 3)];

  const payload = JSON.stringify({
    clienteId: uuidv4(),
    productoId: PRODUCTO_ID,
    nivelRiesgo,
  });

  const res = http.post(`${BASE_URL}/cotizaciones`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(res, {
    'status es 201': (r) => r.status === 201,
  });

  sleep(1);
}