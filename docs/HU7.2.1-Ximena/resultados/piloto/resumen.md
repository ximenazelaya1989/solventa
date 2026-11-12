# Resultados de la corrida `piloto`

- Modo: RETRY_IDEMPOTENCY_ENABLED = **true**
- Inicio: 2026-11-11T21:31:41.465Z | Fin: 2026-11-11T21:33:02.110Z

## Ordenes de pago

| Métrica | Valor |
|---|---|
| Enviadas | 61 |
| Completadas (201) | 61 |
| Fallidas | 0 |
| **Disponibilidad** | **100.000 %** |
| Latencia p50 / p95 / p99 | 85.8 ms / 285.5 ms / 1113.0 ms |
| Órdenes completadas con reintento | 2 |

## Integridad del dinero

| Métrica | Valor |
|---|---|
| Transacciones confirmadas perdidas | 0 |
| Siniestros con pago duplicado | 0 |
| Pagos huérfanos (pagados sin confirmación) | 0 |
| Pagos por réplica | {'ip-172-31-26-69.ec2.internal@us-east-1a': 31, 'ip-172-31-41-240.ec2.internal@us-east-1b': 30} |

## Fallas inyectadas

| Falla | t0 | Detección | Recuperación | Órdenes afectadas | Fuente |
|---|---|---|---|---|---|
| caida_pagos (172.31.26.69@us-east-1a) | 2026-11-11T21:32:04.972+00:00 | 34.9 s | 35.3 s | 2 | Siniestros (CloudWatch) |
| failover_aurora (escritora_previa=solventa-exp006-auroraescritora-yukdyywebl0e) | 2026-11-11T21:32:22.745+00:00 | 13.3 s | 13.7 s | 2 | sonda 200 ms |

Escritora de Aurora: `solventa-exp006-auroraescritora-yukdyywebl0e` → `solventa-exp006-auroraescritora-yukdyywebl0e` (4 escrituras fallidas de la sonda).

## Hipótesis H1

| Criterio | Cumple |
|---|---|
| disponibilidad >= 99.99 % | sí |
| cero transacciones confirmadas perdidas | sí |
| cero pagos duplicados | sí |
| deteccion y recuperacion <= 60 s | sí |

**H1 ACEPTADA**
