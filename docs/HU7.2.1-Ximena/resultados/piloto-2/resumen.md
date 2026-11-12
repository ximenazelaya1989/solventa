# Resultados de la corrida `piloto-2`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **true**
- Inicio: 2026-11-11T21:42:35.177Z | Fin: 2026-11-11T21:45:55.494Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 361 |
| Completadas (201) | 361 |
| Fallidas | 0 |
| **Disponibilidad** | **100.000 %** |
| Latencia p50 / p95 / p99 | 81.4 ms / 117.8 ms / 253.4 ms |
| Órdenes completadas con reintento | 2 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-26-69.ec2.internal@us-east-1a': 181, 'ip-172-31-41-240.ec2.internal@us-east-1b': 180} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.26.69@us-east-1a) | 2026-11-11T21:43:07.118+00:00 | n/a | n/a | 0 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-aurorareplica-wic8exwfqp2p) | 2026-11-11T21:44:05.910+00:00 | 9.1 s | 12.2 s | 2 | sonda 200 ms |

Escritora de Aurora: `solventa-exp006-aurorareplica-wic8exwfqp2p` → `solventa-exp006-auroraescritora-yukdyywebl0e` (13 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | sí |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 ACEPTADA**
