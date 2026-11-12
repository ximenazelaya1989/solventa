# Resultados de la corrida `tacticas-3`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **true**
- Inicio: 2026-11-12T01:44:23.900Z | Fin: 2026-11-12T02:01:24.370Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 10000 |
| Completadas (201) | 10000 |
| Fallidas | 0 |
| **Disponibilidad** | **100.000 %** |
| Latencia p50 / p95 / p99 | 79.0 ms / 123.8 ms / 266.5 ms |
| Órdenes completadas con reintento | 63 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-37-139.ec2.internal@us-east-1b': 1511, 'ip-172-31-27-119.ec2.internal@us-east-1a': 5442, 'ip-172-31-33-186.ec2.internal@us-east-1b': 3047} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.37.139@us-east-1b) | 2026-11-12T01:49:25.912+00:00 | 0.1 s | 0.9 s | 58 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-auroraescritora-yukdyywebl0e) | 2026-11-12T01:54:24.742+00:00 | 17.3 s | 18.9 s | 5 | sonda 200 ms |

Caída de Pagos: ECS retiró la réplica del balanceador a las 2026-11-12T01:50:14.091+00:00 y registró la nueva a las 2026-11-12T01:50:51.755+00:00 (85.8 s después de la caída).

Escritora de Aurora: `solventa-exp006-auroraescritora-yukdyywebl0e` → `solventa-exp006-aurorareplica-wic8exwfqp2p` (1 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | sí |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 ACEPTADA**
