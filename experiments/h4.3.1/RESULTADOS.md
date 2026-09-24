# Resultados y análisis - H4.3.1

## Ejecución en AWS Academy

- Fecha: 24 de septiembre de 2026.
- Región: `us-east-1`.
- Aplicación: tres EC2 `t2.medium` (Ubuntu 24.04), una por zona de
  disponibilidad; PostgreSQL 16 en una cuarta EC2.
- Balanceo: Application Load Balancer `Cheapest-alb`, grupo de destino
  `Cheapest-tg`, health check `GET /health` y tres destinos saludables.
- Generador: k6 0.55.0 desde AWS CloudShell.
- Duración: 15 segundos por nivel; 200, 500, 800, 1.100 y 1.400 TPS.
- Criterios: p95 <= 400 ms, p99 <= 800 ms y errores < 1%.
- Commit desplegado: `12bc015` en la rama
  `experimento-escalabilidad-h4-3-1`; `main` no fue modificado.

La duración corta permite completar el experimento dentro del presupuesto del
laboratorio y comparar tácticas, pero no sustituye una prueba de estabilidad de
dos horas.

### Vertical AWS: una instancia

| CPU / memoria | TPS ofrecidos | TPS logrados | p95 ms | p99 ms | errores % | descartadas |
|---|---:|---:|---:|---:|---:|---:|
| 1 / 1 GiB | 200 | 199,88 | 11,11 | 57,65 | 0,000 | 0 |
| 1 / 1 GiB | 500 | 493,56 | 634,84 | 1.571,83 | 0,000 | 95 |
| 1 / 1 GiB | 800 | 799,85 | 29,56 | 62,37 | 0,000 | 0 |
| 1 / 1 GiB | 1.100 | 919,85 | 1.637,24 | 1.715,96 | 0,000 | 1.852 |
| 1 / 1 GiB | 1.400 | 877,55 | 4.187,90 | 4.904,78 | 0,000 | 6.993 |
| 2 / 2 GiB | 200 | 199,99 | 6,32 | 14,46 | 0,000 | 0 |
| 2 / 2 GiB | 500 | 499,91 | 6,72 | 49,47 | 0,000 | 0 |
| 2 / 2 GiB | 800 | 799,84 | 21,20 | 40,71 | 0,000 | 0 |
| 2 / 2 GiB | 1.100 | 1.001,19 | 1.019,29 | 1.431,81 | 0,000 | 1.096 |
| 2 / 2 GiB | 1.400 | 965,38 | 3.064,70 | 3.236,13 | 0,000 | 5.675 |

El aumento vertical elevó la capacidad útil a 1.100 y 1.400 TPS, pero no logró
sostener el objetivo ni cumplir los percentiles en esos dos niveles. El host
`t2.medium` limita la comparación a 2 vCPU y 4 GiB físicos.

### Horizontal AWS: tres instancias detrás del ALB

| Instancias | CPU / memoria c/u | TPS ofrecidos | TPS logrados | p95 ms | p99 ms | errores % | descartadas |
|---:|---|---:|---:|---:|---:|---:|---:|
| 3 | 1 / 1 GiB | 200 | 199,96 | 9,54 | 15,81 | 0,000 | 0 |
| 3 | 1 / 1 GiB | 500 | 499,86 | 8,48 | 19,30 | 0,000 | 0 |
| 3 | 1 / 1 GiB | 800 | 799,59 | 9,49 | 30,08 | 0,000 | 0 |
| 3 | 1 / 1 GiB | 1.100 | 1.099,59 | 8,25 | 18,40 | 0,000 | 0 |
| 3 | 1 / 1 GiB | 1.400 | 1.399,42 | 9,56 | 40,65 | 0,000 | 0 |

La configuración horizontal cumplió los criterios en todos los niveles y
sostuvo 1.399,42 TPS a la carga máxima, sin errores ni iteraciones descartadas.
Esto equivale a cerca de 10,08 millones de perfiles en dos horas si la tasa se
mantiene.

### Decisión AWS

La hipótesis queda **respaldada en AWS**: para este endpoint y esta carga, tres
instancias pequeñas detrás del ALB superan claramente a una sola instancia con
el doble de CPU y memoria. Se recomienda escalamiento horizontal como táctica
principal, con escalamiento vertical solo como primer ajuste.

## Contexto de ejecución

- Fecha: 24 de septiembre de 2026.
- Entorno: Docker Desktop 29.6.2 sobre macOS; ejecución local.
- Commit: `1a50feb8d83eeae66b2fd1977974567f9d347bfc`.
- Generador: imagen oficial `grafana/k6:latest`, en el mismo equipo físico.
- PostgreSQL 16 limitado a 2 CPU/2 GiB en todas las corridas.
- Duración: 2 minutos por nivel; 200, 500, 800, 1.100 y 1.400 TPS.
- Criterios: p95 <= 400 ms, p99 <= 800 ms y errores < 1%.
- Conversión del ASR: 10 millones / 2 horas = 1.388,89 perfiles/s.

Estos datos son evidencia local reproducible, no una ejecución AWS. Generador y
sistema compartieron el mismo equipo; sirven para comparar tácticas, no como
capacidad definitiva de producción.

## Escalamiento vertical

| CPU / memoria | TPS ofrecidos | TPS logrados | p95 ms | p99 ms | errores % | descartadas |
|---|---:|---:|---:|---:|---:|---:|
| 1 / 1 GiB | 200 | 200,01 | 3,02 | <=800* | 0,000 | 0 |
| 1 / 1 GiB | 500 | 500,01 | 1,06 | <=800* | 0,000 | 0 |
| 1 / 1 GiB | 800 | 800,01 | 0,96 | <=800* | 0,000 | 0 |
| 1 / 1 GiB | 1.100 | 1.099,99 | 1,40 | <=800* | 0,000 | 0 |
| 1 / 1 GiB | 1.400 | 1.372,88 | 5,89 | <=800* | 0,000 | 1.708 |
| 2 / 2 GiB | 200 | 200,00 | 2,32 | 4,43 | 0,000 | 0 |
| 2 / 2 GiB | 500 | 500,00 | 1,21 | 207,20 | 0,000 | 0 |
| 2 / 2 GiB | 800 | 798,09 | 1,15 | 107,83 | 0,000 | 227 |
| 2 / 2 GiB | 1.100 | 1.075,39 | 4,46 | 636,75 | 0,000 | 2.951 |
| 2 / 2 GiB | 1.400 | 1.390,13 | 1,53 | 130,42 | 0,000 | 1.083 |
| 3 / 3 GiB | 200 | 200,00 | 2,69 | 19,94 | 0,000 | 0 |
| 3 / 3 GiB | 500 | 500,00 | 1,01 | 3,06 | 0,000 | 0 |
| 3 / 3 GiB | 800 | 798,64 | 0,98 | 9,96 | 0,000 | 163 |
| 3 / 3 GiB | 1.100 | 1.099,43 | 1,30 | 11,75 | 0,000 | 70 |
| 3 / 3 GiB | 1.400 | 1.390,60 | 1,35 | 11,19 | 0,000 | 1.125 |

\* k6 aprobó el umbral p99 <= 800 ms, pero el primer resumen no conservó el
valor numérico. Se corrigió antes de las demás corridas; no se inventa el dato.

## Escalamiento horizontal

| Instancias | CPU / memoria c/u | TPS ofrecidos | TPS logrados | p95 ms | p99 ms | errores % | descartadas |
|---:|---|---:|---:|---:|---:|---:|---:|
| 3 | 1 / 1 GiB | 200 | 200,00 | 2,70 | 5,09 | 0,000 | 0 |
| 3 | 1 / 1 GiB | 500 | 499,88 | 2,20 | 14,90 | 0,000 | 0 |
| 3 | 1 / 1 GiB | 800 | 799,95 | 1,80 | 7,43 | 0,000 | 0 |
| 3 | 1 / 1 GiB | 1.100 | 1.089,20 | 3,27 | 120,37 | 0,403 | 1.294 |
| 3 | 1 / 1 GiB | 1.400 | 1.399,98 | 2,81 | 12,27 | 0,011 | 0 |

## Análisis

1. Todas las configuraciones aprobaron p95/p99 y mantuvieron errores bajo 1%.
2. La instancia de 1 CPU no sostuvo el objetivo: 1.372,88 perfiles/s es menor a
   1.388,89 y descartó 1.708 iteraciones.
3. Las verticales de 2 y 3 CPU superaron por poco la tasa mínima derivada, pero
   descartaron 1.083 y 1.125 iteraciones a 1.400 TPS.
4. Con recursos totales comparables (3 CPU/3 GiB), horizontal logró 1.399,98 TPS
   sin descartes; vertical logró 1.390,60 TPS con 1.125 descartes.
5. El p99 de 636,75 ms a 1.100 TPS/2 CPU evidencia variabilidad del equipo
   compartido. Cumple, pero debe repetirse en infraestructura controlada.

## Conclusión y decisión

La hipótesis queda **respaldada localmente y en AWS**: varias instancias tras un
balanceador entregaron mayor throughput útil a recursos totales comparables. Se
recomienda escalar horizontalmente el módulo de perfilamiento y conservar el
escalamiento vertical como ajuste inicial o contingencia.

La tasa horizontal equivale a aproximadamente 10,08 millones de perfiles en 2
horas si se sostiene. Aún falta una corrida continua de 2 horas y medir a la vez
el canal en línea, que no existe en el repositorio actual. La ejecución AWS usó
PostgreSQL en EC2 y ALB; una validación posterior puede reemplazar la base por
RDS.

## Evidencias

- JSON y logs locales: `experiments/h4.3.1/results/` en el equipo de ejecución
  (ignorados por Git por tamaño y variabilidad).
- Configuración versionada: Compose vertical/horizontal, Nginx, k6 y `run.sh`.
- Resumen tabular AWS versionado: `experiments/h4.3.1/AWS_RESULTADOS.tsv`.
- Evidencia observada en AWS: tres destinos saludables en el ALB y respuestas
  `HTTP 200` de `/health`; los JSON crudos quedaron además en CloudShell como
  `~/h431-aws-results.tgz`.
- Video: pendiente de grabación por la autora, como se acordó.
