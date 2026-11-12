# Resultados de la corrida `control-2`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **false**
- Inicio: 2026-11-11T23:56:47.298Z | Fin: 2026-11-12T00:13:47.577Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 10000 |
| Completadas (201) | 9953 |
| Fallidas | 47 |
| **Disponibilidad** | **99.530 %** |
| Latencia p50 / p95 / p99 | 78.6 ms / 125.1 ms / 270.7 ms |
| Órdenes completadas con reintento | 0 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-19-70.ec2.internal@us-east-1a': 5383, 'ip-172-31-44-126.ec2.internal@us-east-1b': 1510, 'ip-172-31-33-240.ec2.internal@us-east-1b': 3062} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.44.126@us-east-1b) | 2026-11-12T00:01:49.294+00:00 | 0.1 s | n/a | 42 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-aurorareplica-wic8exwfqp2p) | 2026-11-12T00:06:48.061+00:00 | 6.4 s | 8.9 s | 5 | sonda 200 ms |

Caída de Pagos: ECS retiró la réplica del balanceador a las 2026-11-12T00:02:33.976+00:00 y registró la nueva a las 2026-11-12T00:03:11.397+00:00 (82.1 s después de la caída).

Escritora de Aurora: `solventa-exp006-aurorareplica-wic8exwfqp2p` → `solventa-exp006-auroraescritora-yukdyywebl0e` (10 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | **no** |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 REFUTADA**
