# EXP-009 · Guía de despliegue en AWS Academy

Pasos para correr el experimento en AWS (región **us-east-1**). Los nombres exactos de la consola pueden variar un poco;
si el Learner Lab bloquea algún servicio, avisa y se adapta.

> Todo cuesta créditos mientras esté encendido. **Apaga todo al terminar** (último apartado).

## 0. Antes de empezar

- Inicia el lab (Start Lab) y abre la consola. El rol disponible es **LabRole**: se usa como rol de ejecución y de tarea en ECS (no se pueden crear roles nuevos).
- La sesión del lab dura unas horas: planea hacer las corridas de una sola vez y guardar los resultados al final de cada una.
- Instala y configura la AWS CLI con las credenciales del lab (están en "AWS Details" del lab; cambian en cada sesión).

## 1. Qué se despliega

| Servicio | Imagen (ECR) | Tareas | Puerto | Health check del ALB |
|---|---|---:|---:|---|
| api-gateway | `api-gateway` | 2 | 3000 | `/health` |
| cotizacion | `cotizacion` | 2 | 8000 | `/health` |
| perfilamiento | `perfilamiento` | 2 (1 worker por tarea) | 8000 | `/ready` (solo verifica Redis) |
| mock-open-finance | `mock-open-finance` | 1 | 8000 | `/health` |

Datos: **RDS PostgreSQL** (`cotizacion_db`, `perfilamiento_db`) y **ElastiCache Redis** (1 nodo). Carga: una **EC2** con Locust.
Tareas Fargate de 0,25 vCPU / 0,5 GB bastan.

## 2. Subir las imágenes a ECR

Crea 4 repositorios (`api-gateway`, `cotizacion`, `perfilamiento`, `mock-open-finance`) y, desde la raíz del repo:

```bash
ACCOUNT=<tu-id-de-cuenta>; REGION=us-east-1
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com
for s in api-gateway cotizacion perfilamiento mock-open-finance; do
  docker build --platform linux/amd64 -t $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/$s:latest services/$s
  docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/$s:latest
done
```

## 3. Red y seguridad (VPC por defecto)

Crea cuatro security groups:

| SG | Entrada |
|---|---|
| `sg-alb` | 80 desde Internet |
| `sg-servicios` | 3000 y 8000 desde `sg-alb` y desde `sg-servicios` mismo y desde `sg-carga` |
| `sg-datos` | 5432 (RDS) y 6379 (Redis) desde `sg-servicios` y `sg-carga` |
| `sg-carga` | 22 desde tu IP |

## 4. Datos

1. **RDS PostgreSQL** (`db.t3.micro`, usuario/clave a tu elección, `sg-datos`). Desde la EC2 de carga crea las dos bases:
   `CREATE DATABASE cotizacion_db; CREATE DATABASE perfilamiento_db;` (los servicios crean sus tablas al arrancar).
2. **ElastiCache Redis** (`cache.t3.micro`, **un solo nodo**, `sg-datos`). Anota el endpoint.

## 5. Un solo ALB con reglas por ruta

Crea un ALB (internet-facing, `sg-alb`) y cuatro *target groups* (tipo **IP**, uno por servicio) con los health checks de la tabla.
Reglas del listener (puerto 80):

| Ruta | Target group |
|---|---|
| `/v1/*` | api-gateway |
| `/cotizaciones*` | cotizacion |
| `/perfiles*`, `/ready`, `/admin/open-finance/*` | perfilamiento |
| `/senales/*`, `/admin/fail`, `/admin/estado`, `/admin/reset` | mock-open-finance |

Así los servicios se llaman entre sí por el DNS del ALB (`ALB_DNS`). Si el lab permite **ECS Service Connect / Cloud Map**, se puede usar en su lugar.

## 6. ECS

Cluster Fargate; un *task definition* por servicio con **LabRole** como rol de ejecución y de tarea, logs a CloudWatch (`awslogs`), y estas variables:

**api-gateway**
`SERVICE_NAME=api-gateway`, `COTIZACION_URL=http://ALB_DNS`

**cotizacion**
`SERVICE_NAME=cotizacion`, `DATABASE_URL=postgresql+psycopg://USER:CLAVE@RDS_ENDPOINT:5432/cotizacion_db`,
`PERFILAMIENTO_URL=http://ALB_DNS`, `PERFILAMIENTO_TIMEOUT_S=0.2`

**perfilamiento**
`SERVICE_NAME=perfilamiento`, `DATABASE_URL=postgresql+psycopg://USER:CLAVE@RDS_ENDPOINT:5432/perfilamiento_db`,
`REDIS_URL=redis://REDIS_ENDPOINT:6379/0`, `OPEN_FINANCE_ENABLED=true`, `OPEN_FINANCE_URL=http://ALB_DNS`,
`OPEN_FINANCE_ADMIN_ENABLED=true`, **`CIRCUIT_BREAKER_ENABLED=true` (B) o `false` (A)**

**mock-open-finance**
`SERVICE_NAME=mock-open-finance`

Un *service* por task definition con los números de tareas de la tabla, `sg-servicios` y el target group correspondiente.
Verifica que todos queden *healthy* y que `http://ALB_DNS/v1/cotizaciones` (POST) responda.

## 7. La EC2 de carga

`t3.small` Amazon Linux (`sg-carga`, misma VPC). Instala lo necesario y trae los scripts:

```bash
sudo dnf install -y python3-pip git postgresql15
git clone <url-del-repo> && cd <repo>/docs/HU10.1.3-Giovanna/experimento
pip3 install -r requirements.txt
```

Direcciones privadas de **cada tarea de Perfilamiento** (consola ECS → tarea → red → IP privada), para leer el estado del circuito de cada una:
`PERF_ADMIN_URLS=http://10.0.x.x:8000,http://10.0.y.y:8000`

## 8. Las corridas (cada una dura 20 min)

Corridas previstas: **B con `error503`**, **B con `lento2s`** y **A con `error503`**. Para cada una:

1. Ajusta `CIRCUIT_BREAKER_ENABLED` en el task definition de Perfilamiento (B = `true`, A = `false`) y fuerza un nuevo despliegue. Actualiza `PERF_ADMIN_URLS` (las IP cambian).
2. Prepara los datos y limpia la caché:
   `python3 preparar_datos.py --perf http://ALB_DNS --redis redis://REDIS_ENDPOINT:6379/0`
3. Lanza la carga:

```bash
SALIDA=resultados/B1 MODO_FALLA=error503 \
MOCK_URL=http://ALB_DNS PERF_ADMIN_URLS=http://10.0.x.x:8000,http://10.0.y.y:8000 \
locust -f locustfile.py --headless --host http://ALB_DNS -u 10 -r 10
```

4. Al terminar: `python3 analizar.py resultados/B1`.
5. Copia `resultados/` a tu computador (scp) y a `docs/HU10.1.3-Giovanna/resultados/`.

Los cambios de estado del circuito también quedan en CloudWatch Logs de Perfilamiento (busca `evento=CIRCUITO`).

## 9. Evidencia para el PDF

- Capturas de la consola: servicios ECS, tareas *healthy*, target groups, RDS, ElastiCache, EC2.
- `resumen.md` y `resumen.json` de cada corrida, y los `requests.csv`.
- Logs de CloudWatch con `evento=CIRCUITO` y `evento=DEGRADADO`.
- El PDF de resultados y análisis, en esta carpeta (`docs/HU10.1.3-Giovanna/`).

## 10. Video (máximo 8 min), en este orden

1. Contexto: el experimento y la hipótesis, en pocas palabras.
2. Despliegue: la consola de AWS con los servicios (ECS, ALB, RDS, ElastiCache).
3. Tácticas: dónde está cada una en el código (`open_finance.py`) y en la configuración (flags, health check `/ready`, pool de 10, timeout de 120 ms).
4. Ejecución: la prueba en curso (Locust), la falla inyectada y cómo el circuito abre y la cotización sigue respondiendo.

## 11. Al terminar: apagar todo

Elimina los *services* y el cluster de ECS, el ALB y los target groups, RDS, ElastiCache, la EC2 y los repositorios de ECR si ya no los necesitas.
Verifica en la consola que no quede nada en ejecución.
