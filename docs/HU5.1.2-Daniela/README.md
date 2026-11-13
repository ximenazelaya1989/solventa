# EXP-008 · HU5.1.2 · Cuota por socio en el API Gateway (Daniela)

**ASR (escalabilidad).** Cuando un socio sube su tráfico de 1x a 10x en un minuto, las cotizaciones de los demás socios mantienen p95 < 250 ms y p99 < 500 ms.

**Táctica.** Limitación de tasa por socio con token bucket en Redis, aplicada en el API Gateway. Cada socio se identifica por su credencial (`x-api-key`) y tiene su propio balde. El exceso recibe `429` con `Retry-After` antes de llegar a Cotización y Perfilamiento.

## Dónde está cada cosa

| Qué | Archivo |
|---|---|
| Guard de la cuota (lee el flag, identifica al socio, responde 429) | `services/api-gateway/src/cuota-socio/cuota-socio.guard.ts` |
| Token bucket atómico (script Lua en Redis) | `services/api-gateway/src/cuota-socio/token-bucket.ts` |
| Registro como guard global | `services/api-gateway/src/cuota-socio/cuota-socio.module.ts` y una línea en `app.module.ts` |
| Infraestructura AWS (ECS Fargate, 2 RDS, ElastiCache, 2 ALB, EC2 JMeter) | `experimento/infra/exp008.yaml` |
| Plan de JMeter (Open Model Thread Group por socio) | `experimento/carga/generar_plan.py` |
| Siembra de 10.000 perfiles | `experimento/carga/sembrar_perfiles.py` |
| Orquestación de las corridas | `experimento/scripts/orquestar.py` |
| Análisis y figuras | `experimento/analisis/analizar.py` |
| Datos crudos y métricas | `resultados/` |
| Resultados y análisis | `EXP-008_HU5.1.2_Resultados_y_Analisis.pdf` |

## Variables del gateway

| Variable | Por defecto | Uso |
|---|---|---|
| `RATE_LIMIT_ENABLED` | `false` | Activa la cuota. Apagada, el gateway se comporta como la base compartida. |
| `RATE_LIMIT_RPS` | `20` | Fichas por segundo por socio (en el experimento, 0,2C). |
| `RATE_LIMIT_BURST_S` | `2` | Ráfaga, en segundos de cuota. |
| `RATE_LIMIT_REDIS_TIMEOUT_MS` | `50` | Si Redis tarda más, la petición pasa (fail-open). |
| `REDIS_URL` | `redis://localhost:6379/1` | Redis de cuotas. |

Con la cuota activa, una petición a `/v1/*` sin `x-api-key` recibe `401`. `/health` nunca pasa por la cuota.

## Prueba rápida en local

```bash
RATE_LIMIT_ENABLED=true RATE_LIMIT_RPS=5 docker compose up -d --build api-gateway
for i in $(seq 20); do
  curl -s -o /dev/null -w "%{http_code} " -X POST http://localhost:18080/v1/cotizaciones \
    -H 'content-type: application/json' -H 'x-api-key: socio-a' \
    -d '{"clienteId":"11111111-1111-1111-1111-111111111111","productoId":"22222222-2222-2222-2222-222222222222"}'
done   # unas 10 respuestas 201 (la ráfaga) y luego 429
```

## Resultado

C calibrada = 60 cotizaciones/s. A, B y C a 9/s, D de 9 a 90/s (10x), cuota de 12/s por socio.

| Condición | A, B y C en la ventana (min 3 a 10) | Socio D en el pico |
|---|---|---|
| Sin cuota (corridas 1, 3 y 5) | 85,7 % a 88,8 % de error, p95 fuera de medida. ECS reemplazó 2 veces la tarea de Cotización en cada corrida | casi todo 503 o timeout |
| Con cuota (corridas 2, 4 y 6) | p95 de 43 a 86 ms, p99 de 129 a 1.030 ms, 2 errores en 34.162 peticiones | 12 aceptadas/s, el resto 429 |

Hipótesis **parcialmente validada**: el p95 cumple con holgura, el p99 superó 500 ms en 4 de 9 mediciones por pausas de Cotización que también aparecen antes del pico de D. Detalle en el PDF.

## Reproducir en AWS Academy

Con las credenciales del Learner Lab en `~/.aws/credentials`:

```bash
cd docs/HU5.1.2-Daniela/experimento
python3 scripts/orquestar.py preparar                 # bucket S3 y codigo
python3 scripts/orquestar.py desplegar --desired 0    # stack sin tareas
python3 scripts/orquestar.py lanzar imagenes          # build y push a ECR desde la EC2
python3 scripts/orquestar.py desplegar --desired 1
python3 scripts/orquestar.py registrar-td --c 60      # gateway sin cuota y con cuota (0,2C)
python3 scripts/orquestar.py lanzar sembrar           # 10.000 perfiles
python3 scripts/orquestar.py lanzar calibrar 60 30 10 calibracion_2
python3 scripts/orquestar.py lanzar corridas 60       # 6 corridas alternadas, unos 115 min
python3 scripts/orquestar.py progreso                 # ver avance
python3 scripts/orquestar.py descargar                # JTL, CloudWatch y corridas.json a resultados/
python3 analisis/resumen_informe.py ../resultados     # tablas, figuras y veredicto
python3 scripts/orquestar.py borrar
```

Las corridas largas las ejecuta `scripts/runner_ec2.sh` en la EC2 de JMeter, así no dependen de que siga conectada la máquina que las lanza.
