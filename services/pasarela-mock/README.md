# Pasarela de pagos (mock)

Sistema externo simulado para EXP-006 (H7.2.1, Ximena). Aprueba cada desembolso que le envía Pagos y respeta la llave de idempotencia del encabezado `Idempotency-Key`: si la misma llave llega dos veces, devuelve la misma transacción y no paga dos veces.

No tiene dependencias ni base de datos (guarda las transacciones en memoria).

```bash
node server.js                       # puerto 8080
curl -X POST localhost:8080/desembolsos -H 'idempotency-key: abc' -d '{}'
curl localhost:8080/estadisticas
```

Variables: `PORT` (8080) y `PASARELA_LATENCIA_MS` (50, latencia simulada).
