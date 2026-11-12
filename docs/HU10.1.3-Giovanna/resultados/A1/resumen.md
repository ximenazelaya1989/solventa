# Resumen de la corrida `A1`

Circuit breaker: **apagado (A)** · modo de falla: `error503` · 10 TPS · fases 300/600/300 s

Disponibilidad total: **49.987 %** (5996/11995)

| Fase | Solicitudes | Fallos | Disponibilidad | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|
| 1 normal | 2998 | 0 | 100.0 % | 96.7 | 164.5 |
| 2 falla | 5996 | 5996 | 0.0 % | 30.3 | 102.4 |
| 3 recuperacion | 3001 | 3 | 99.9 % | 99.3 | 171.5 |

Criterio de la fase de falla (<= 0,1 % de fallos): 5996 fallos, maximo 5 -> **NO CUMPLE**
Tiempo de deteccion (falla -> circuito ABIERTO): None s (meta <= 5 s)
Tiempo de recuperacion (restauracion -> CERRADO): None s
Servidas desde cache: None % · con perfil por defecto: None %
