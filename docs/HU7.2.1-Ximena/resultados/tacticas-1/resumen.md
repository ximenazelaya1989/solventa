# Resultados de la corrida `tacticas-1`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **true**
- Inicio: 2026-11-11T22:38:40.251Z | Fin: 2026-11-11T22:55:40.625Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 10001 |
| Completadas (201) | 10001 |
| Fallidas | 0 |
| **Disponibilidad** | **100.000 %** |
| Latencia p50 / p95 / p99 | 80.8 ms / 161.2 ms / 375.1 ms |
| Órdenes completadas con reintento | 74 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-47-77.ec2.internal@us-east-1b': 1510, 'ip-172-31-23-103.ec2.internal@us-east-1a': 5534, 'ip-172-31-45-172.ec2.internal@us-east-1b': 2957} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.47.77@us-east-1b) | 2026-11-11T22:43:42.196+00:00 | 0.2 s | 0.3 s | 68 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-aurorareplica-wic8exwfqp2p) | 2026-11-11T22:48:40.930+00:00 | 15.1 s | 16.1 s | 6 | sonda 200 ms |

Caída de Pagos: ECS retiró la réplica del balanceador a las 2026-11-11T22:44:36.419+00:00 y registró la nueva a las 2026-11-11T22:45:25.413+00:00 (103.2 s después de la caída).

Escritora de Aurora: `solventa-exp006-aurorareplica-wic8exwfqp2p` → `solventa-exp006-auroraescritora-yukdyywebl0e` (2 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | sí |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 ACEPTADA**
