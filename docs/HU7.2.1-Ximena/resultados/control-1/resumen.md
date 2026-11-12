# Resultados de la corrida `control-1`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **false**
- Inicio: 2026-11-11T23:36:03.794Z | Fin: 2026-11-11T23:53:04.586Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 10001 |
| Completadas (201) | 9937 |
| Fallidas | 64 |
| **Disponibilidad** | **99.360 %** |
| Latencia p50 / p95 / p99 | 78.7 ms / 135.5 ms / 325.5 ms |
| Órdenes completadas con reintento | 0 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-44-126.ec2.internal@us-east-1b': 5377, 'ip-172-31-26-192.ec2.internal@us-east-1a': 1509, 'ip-172-31-19-70.ec2.internal@us-east-1a': 3054} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.26.192@us-east-1a) | 2026-11-11T23:41:05.802+00:00 | 0.4 s | n/a | 60 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-auroraescritora-yukdyywebl0e) | 2026-11-11T23:46:04.022+00:00 | 10.4 s | 12.8 s | 4 | sonda 200 ms |

Caída de Pagos: ECS retiró la réplica del balanceador a las 2026-11-11T23:41:51.589+00:00 y registró la nueva a las 2026-11-11T23:42:30.066+00:00 (84.3 s después de la caída).

Escritora de Aurora: `solventa-exp006-auroraescritora-yukdyywebl0e` → `solventa-exp006-aurorareplica-wic8exwfqp2p` (9 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | **no** |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 REFUTADA**
