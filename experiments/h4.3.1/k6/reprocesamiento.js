import http from 'k6/http';
import { check } from 'k6';
import exec from 'k6/execution';

const rate = Number(__ENV.RATE || 200);

export const options = {
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  scenarios: {
    reprocesamiento: {
      executor: 'constant-arrival-rate',
      rate,
      timeUnit: '1s',
      duration: __ENV.DURATION || '2m',
      preAllocatedVUs: Number(__ENV.PRE_ALLOCATED_VUS || 300),
      maxVUs: Number(__ENV.MAX_VUS || 2000),
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<=400', 'p(99)<=800'],
    http_req_failed: ['rate<0.01'],
  },
};

function uuidFromNumber(value) {
  const suffix = String(value % 1_000_000_000_000).padStart(12, '0');
  return `00000000-0000-4000-8000-${suffix}`;
}

export default function () {
  const sequence =
    Number(__ENV.RUN_OFFSET || 0) + exec.scenario.iterationInTest;
  const payload = JSON.stringify({
    clienteId: uuidFromNumber(sequence),
    señalesOpenData: {
      ingresoMensual: 2_000_000 + (sequence % 18_000_000),
      deudaTotal: sequence % 100_000_000,
      indicePago: (sequence % 100) / 100,
    },
  });

  const response = http.post(
    `${__ENV.BASE_URL || 'http://localhost:8080'}/perfilamiento/reprocesar`,
    payload,
    { headers: { 'Content-Type': 'application/json' } },
  );

  check(response, { 'HTTP 200': (result) => result.status === 200 });
}

export function handleSummary(data) {
  const output = __ENV.SUMMARY_FILE || 'summary.json';
  return { [output]: JSON.stringify(data, null, 2), stdout: '' };
}
