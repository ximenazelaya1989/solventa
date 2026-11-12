# Resumen de la corrida `B1`

Circuit breaker: **activado (B)** · modo de falla: `error503` · 10 TPS · fases 300/600/300 s

Disponibilidad total: **99.958 %** (11989/11994)

| Fase | Solicitudes | Fallos | Disponibilidad | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|
| 1 normal | 2997 | 1 | 99.967 % | 103.4 | 211.2 |
| 2 falla | 5995 | 0 | 100.0 % | 39.1 | 134.0 |
| 3 recuperacion | 3002 | 4 | 99.867 % | 103.9 | 206.3 |

Criterio de la fase de falla (<= 0,1 % de fallos): 0 fallos, maximo 5 -> **CUMPLE**
Tiempo de deteccion (falla -> circuito ABIERTO): 1.102 s (meta <= 5 s)
Tiempo de recuperacion (restauracion -> CERRADO): 3.019 s
Servidas desde cache: 78.9 % · con perfil por defecto: 21.1 %
