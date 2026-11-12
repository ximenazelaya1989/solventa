# Resumen de la corrida `A2`

Circuit breaker: **apagado (A)** · modo de falla: `lento2s` · 10 TPS · fases 300/600/300 s

Disponibilidad total: **49.908 %** (5984/11990)

| Fase | Solicitudes | Fallos | Disponibilidad | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|
| 1 normal | 2998 | 3 | 99.9 % | 98.5 | 167.6 |
| 2 falla | 5992 | 5992 | 0.0 % | 158.5 | 233.9 |
| 3 recuperacion | 3000 | 11 | 99.633 % | 100.1 | 209.9 |

Criterio de la fase de falla (<= 0,1 % de fallos): 5992 fallos, maximo 5 -> **NO CUMPLE**
Tiempo de deteccion (falla -> circuito ABIERTO): None s (meta <= 5 s)
Tiempo de recuperacion (restauracion -> CERRADO): None s
Servidas desde cache: None % · con perfil por defecto: None %
