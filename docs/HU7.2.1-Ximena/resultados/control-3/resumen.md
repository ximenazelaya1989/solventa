# Resultados de la corrida `control-3`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **false**
- Inicio: 2026-11-12T00:57:07.962Z | Fin: 2026-11-12T01:14:08.587Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 10001 |
| Completadas (201) | 9950 |
| Fallidas | 51 |
| **Disponibilidad** | **99.490 %** |
| Latencia p50 / p95 / p99 | 78.9 ms / 133.2 ms / 279.2 ms |
| Órdenes completadas con reintento | 0 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-34-88.ec2.internal@us-east-1b': 1509, 'ip-172-31-19-28.ec2.internal@us-east-1a': 5343, 'ip-172-31-44-155.ec2.internal@us-east-1b': 3099} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.34.88@us-east-1b) | 2026-11-12T01:02:09.963+00:00 | 0.3 s | n/a | 46 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-auroraescritora-yukdyywebl0e) | 2026-11-12T01:07:08.842+00:00 | 18.4 s | 19.7 s | 5 | sonda 200 ms |

Caída de Pagos: ECS retiró la réplica del balanceador a las 2026-11-12T01:02:47.214+00:00 y registró la nueva a las 2026-11-12T01:03:24.789+00:00 (74.8 s después de la caída).

Escritora de Aurora: `solventa-exp006-auroraescritora-yukdyywebl0e` → `solventa-exp006-aurorareplica-wic8exwfqp2p` (3 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | **no** |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 REFUTADA**
