# Comparación de corridas - EXP-006 (H7.2.1)

| Corrida | Modo | Enviadas | Completadas | Disponibilidad | Perdidas | Duplicados | Huérfanos | Caída Pagos det./rec. (s) | Failover Aurora det./rec. (s) | p99 (ms) | H1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| control-1 | control | 10001 | 9937 | 99.360 % | 0 | 0 | 0 | 0.4 / n/a | 10.4 / 12.8 | 326 | REFUTADA |
| control-2 | control | 10000 | 9953 | 99.530 % | 0 | 0 | 0 | 0.1 / n/a | 6.4 / 8.9 | 271 | REFUTADA |
| control-3 | control | 10001 | 9950 | 99.490 % | 0 | 0 | 0 | 0.3 / n/a | 18.4 / 19.7 | 279 | REFUTADA |
| piloto | tácticas | 61 | 61 | 100.000 % | 0 | 0 | 0 | 34.9 / 35.3 | 13.3 / 13.7 | 1113 | ACEPTADA |
| piloto-2 | tácticas | 361 | 361 | 100.000 % | 0 | 0 | 0 | n/a / n/a | 9.1 / 12.2 | 253 | ACEPTADA |
| piloto-3 | tácticas | 360 | 360 | 100.000 % | 0 | 0 | 0 | 1.2 / 1.3 | 8.5 / 10.1 | 252 | ACEPTADA |
| tacticas-1 | tácticas | 10001 | 10001 | 100.000 % | 0 | 0 | 0 | 0.2 / 0.3 | 15.1 / 16.1 | 375 | ACEPTADA |
| tacticas-2 | tácticas | 10001 | 10001 | 100.000 % | 0 | 0 | 0 | 0.1 / 0.3 | 5.6 / 8.3 | 385 | ACEPTADA |
| tacticas-3 | tácticas | 10000 | 10000 | 100.000 % | 0 | 0 | 0 | 0.1 / 0.9 | 17.3 / 18.9 | 267 | ACEPTADA |