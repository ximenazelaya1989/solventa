import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  duration: '10m',
  vus: 10,
  thresholds: {
    http_req_duration: [
      'p(95)<400',
      'p(99)<800'
    ],
    http_req_failed: [
      'rate<0.05'
    ]
  }
};

export default function () {
  const payload = JSON.stringify({
    cotizacionId: "33333333-3333-3333-3333-333333333333"
  });

  const params = {
    headers: {
      'Content-Type': 'application/json'
    }
  };

  const res = http.post(
    'http://localhost:3000/suscripciones',
    payload,
    params
  );

  check(res, {
    'status 200 o 201': (r) =>
      r.status === 200 || r.status === 201
  });

  sleep(1);
}
