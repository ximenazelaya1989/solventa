# Resumen de la corrida `B2`

Circuit breaker: **activado (B)** · modo de falla: `lento2s` · 10 TPS · fases 300/600/300 s

Disponibilidad total: **99.975 %** (11991/11994)

| Fase | Solicitudes | Fallos | Disponibilidad | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|
| 1 normal | 2998 | 3 | 99.9 % | 101.5 | 202.6 |
| 2 falla | 5992 | 0 | 100.0 % | 66.7 | 155.2 |
| 3 recuperacion | 3004 | 0 | 100.0 % | 101.0 | 179.3 |

Criterio de la fase de falla (<= 0,1 % de fallos): 0 fallos, maximo 5 -> **CUMPLE**
Tiempo de deteccion (falla -> circuito ABIERTO): 1.151 s (meta <= 5 s)
Tiempo de recuperacion (restauracion -> CERRADO): 8.325 s
Servidas desde cache: 80.7 % · con perfil por defecto: 19.3 %
