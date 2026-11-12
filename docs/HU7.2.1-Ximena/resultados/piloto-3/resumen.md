# Resultados de la corrida `piloto-3`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **true**
- Inicio: 2026-11-11T21:54:39.746Z | Fin: 2026-11-11T21:58:00.154Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 360 |
| Completadas (201) | 360 |
| Fallidas | 0 |
| **Disponibilidad** | **100.000 %** |
| Latencia p50 / p95 / p99 | 83.6 ms / 170.2 ms / 252.2 ms |
| Órdenes completadas con reintento | 20 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-21-255.ec2.internal@us-east-1a': 33, 'ip-172-31-47-77.ec2.internal@us-east-1b': 260, 'ip-172-31-23-103.ec2.internal@us-east-1a': 67} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.21.255@us-east-1a) | 2026-11-11T21:55:11.688+00:00 | 1.2 s | 1.3 s | 19 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-auroraescritora-yukdyywebl0e) | 2026-11-11T21:56:10.446+00:00 | 8.5 s | 10.1 s | 1 | sonda 200 ms |

Caída de Pagos: ECS retiró la réplica del balanceador a las 2026-11-11T21:55:43.101+00:00 y registró la nueva a las 2026-11-11T21:56:30.216+00:00 (78.5 s después de la caída).

Escritora de Aurora: `solventa-exp006-auroraescritora-yukdyywebl0e` → `solventa-exp006-aurorareplica-wic8exwfqp2p` (1 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | sí |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 ACEPTADA**
