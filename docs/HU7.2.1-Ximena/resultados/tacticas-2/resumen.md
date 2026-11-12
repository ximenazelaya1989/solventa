# Resultados de la corrida `tacticas-2`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **true**
- Inicio: 2026-11-12T01:23:40.395Z | Fin: 2026-11-12T01:40:41.030Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 10001 |
| Completadas (201) | 10001 |
| Fallidas | 0 |
| **Disponibilidad** | **100.000 %** |
| Latencia p50 / p95 / p99 | 80.8 ms / 163.7 ms / 384.7 ms |
| Órdenes completadas con reintento | 77 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-27-119.ec2.internal@us-east-1a': 5456, 'ip-172-31-43-21.ec2.internal@us-east-1b': 1511, 'ip-172-31-37-139.ec2.internal@us-east-1b': 3034} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.43.21@us-east-1b) | 2026-11-12T01:28:42.667+00:00 | 0.1 s | 0.3 s | 72 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-aurorareplica-wic8exwfqp2p) | 2026-11-12T01:33:41.549+00:00 | 5.6 s | 8.3 s | 5 | sonda 200 ms |

Caída de Pagos: ECS retiró la réplica del balanceador a las 2026-11-12T01:29:23.851+00:00 y registró la nueva a las 2026-11-12T01:30:11.190+00:00 (88.5 s después de la caída).

Escritora de Aurora: `solventa-exp006-aurorareplica-wic8exwfqp2p` → `solventa-exp006-auroraescritora-yukdyywebl0e` (11 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | sí |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 ACEPTADA**
