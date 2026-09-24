# Experimento individual H4.3.1 - escalabilidad

El informe consolidado listo para revisión está en
`output/pdf/Informe_Experimento_H4_3_1.pdf`; los valores fuente y la decisión se
mantienen también en [RESULTADOS.md](./RESULTADOS.md).

## Correspondencia con la aplicación

La HU4.3.1 pide recalcular al menos 10 millones de perfiles en menos de dos
horas al incorporar nuevas fuentes de Open Data. Esto exige un promedio de
1.388,89 perfiles/s; el último nivel se redondea a 1.400 transacciones/s.

El repositorio original solo tenía la entidad `PerfilRiesgo` y una lectura de
score. Este cambio agrega el mínimo flujo ejecutable: cada `POST
/perfilamiento/reprocesar` recibe señales Open Data, calcula un score y hace
`upsert` por `clienteId`. Una transacción exitosa equivale a un perfil
reprocesado. La operación es idempotente para que repetir un cliente no cree
duplicados.

Este experimento **no demuestra todavía** el requisito completo de 10 millones
ni que el canal en línea no se degrade: no existe en el repositorio un canal de
consulta de perfil listo para medir en paralelo. Sí prueba el caudal y las
latencias del flujo de reprocesamiento que la aplicación realmente implementa.

## Hipótesis y criterios

- Hipótesis: el escalamiento horizontal de tres instancias de 1 CPU/1 GiB detrás
  de un balanceador mantendrá mayor throughput útil que una instancia vertical
  con recursos totales comparables (3 CPU/3 GiB).
- Carga ofrecida, en orden: 200, 500, 800, 1.100 y 1.400 TPS.
- Aceptación por nivel: p95 <= 400 ms, p99 <= 800 ms y errores < 1%.
- El throughput logrado se toma de `http_reqs.rate` y debe compararse con la
  carga ofrecida. También se revisa `dropped_iterations`; si es mayor que cero,
  el generador no logró sostener la tasa solicitada.

## Requisitos

- Docker con Compose.
- k6 instalado en una máquina distinta al servidor en la medición AWS. Para el
  ensayo local, si k6 no está instalado el script usa automáticamente su imagen
  oficial de Docker. Ejecutar carga y aplicación en la misma máquina solo sirve
  como ensayo local.
- Puertos 8080 (entrada) y 5432 (interno, no publicado) disponibles.

## Ensayo reproducible local

Desde la raíz del repositorio:

```bash
npm ci
npm test
npm run build

# Escalamiento vertical, configuración comparable de 3 CPU/3 GiB
API_CPUS=3 API_MEMORY=3g npm run experiment:h431 -- vertical

# Escalamiento horizontal, 3 instancias de 1 CPU/1 GiB + Nginx
INSTANCE_CPUS=1 INSTANCE_MEMORY=1g npm run experiment:h431 -- horizontal
```

Para evidenciar la progresión vertical, repetir con recursos crecientes:

```bash
API_CPUS=1 API_MEMORY=1g npm run experiment:h431 -- vertical
API_CPUS=2 API_MEMORY=2g npm run experiment:h431 -- vertical
API_CPUS=3 API_MEMORY=3g npm run experiment:h431 -- vertical
```

Cada ejecución crea una carpeta UTC bajo `results/<modo>/` con un JSON resumen
por nivel, configuración y logs. Esos archivos se ignoran en Git para evitar
presentar datos inventados o accidentales. No se genera CSV por defecto porque
una matriz completa puede ocupar varios GiB; agréguese `--out csv=...` a k6 solo
si hay espacio suficiente. La duración por nivel es 2 minutos; para un ensayo
rápido se puede usar `DURATION=10s RATES="200 500"`.

## Ejecución en AWS y evidencia

La ejecución realizada el 24 de septiembre de 2026 usó AWS Academy en
`us-east-1`: tres EC2 `t2.medium` para la aplicación, una EC2 para PostgreSQL
16, un Application Load Balancer y k6 0.55.0 desde CloudShell. Las corridas
duraron 15 segundos por nivel para proteger el presupuesto académico. Los
resultados observados están en [RESULTADOS.md](./RESULTADOS.md), los valores
exactos en [AWS_RESULTADOS.tsv](./AWS_RESULTADOS.tsv) y el informe consolidado
en `output/pdf/Informe_Experimento_H4_3_1.pdf`. Los JSON crudos permanecen en
CloudShell como `~/h431-aws-results.tgz`.

Las instrucciones siguientes describen una reproducción más cercana a un
entorno de producción con ECR/RDS y una duración mayor; no deben confundirse
con la infraestructura económica utilizada para obtener los resultados ya
registrados.

No había infraestructura AWS en el repositorio. La forma mínima de reproducir
el experimento sin confundir un ensayo local con evidencia AWS es:

1. Construir la imagen con el `Dockerfile` y publicarla en ECR.
2. Crear PostgreSQL 16 en RDS y conservar exactamente la misma clase, parámetros
   y datos para ambas tácticas. No exponerlo a Internet.
3. Usar una base dedicada al experimento y definir `NODE_ENV=experiment` junto
   con las variables `DB_*`, para que TypeORM cree el esquema que este proyecto
   aún no gestiona con migraciones. No usar esta opción en una base productiva.
4. Vertical: ejecutar una tarea/instancia de la API y repetir con 1/1, 2/2 y
   3 vCPU/GiB. Apuntar k6 directamente al endpoint de esa única instancia.
5. Horizontal: iniciar una tarea para crear el esquema y luego escalar a tres
   tareas/instancias de 1 vCPU/1 GiB en el mismo grupo
   objetivo detrás de un Application Load Balancer. Apuntar k6 al DNS del ALB.
6. Ejecutar k6 desde otra EC2 en la misma región y VPC. Para cada modo:

```bash
BASE_URL="http://DNS-DEL-ALB" RATE=200 DURATION=2m \
  SUMMARY_FILE=summary-200-tps.json \
  k6 run experiments/h4.3.1/k6/reprocesamiento.js
```

Repetir el comando con 500, 800, 1.100 y 1.400. Antes de cada comparación usar
la misma base limpia/restaurada y dejar un periodo de enfriamiento. Mantener la
misma versión de imagen, zona/región, RDS y generador de carga. Capturar CPU y
memoria de ECS/EC2, conexiones/CPU/IOPS de RDS y `HealthyHostCount`/latencia del
ALB. Si RDS se satura, la prueba mide la base de datos y no la táctica de escala
de la API; debe registrarse como limitación, no ocultarse.

## Video de máximo 5 minutos

Mostrar, en este orden: ASR e hipótesis (30 s); consola AWS con despliegue
vertical y luego grupo de tres instancias/ALB (60 s); recorrido por controller,
service, k6 y Compose (60 s); ejecución visible de un nivel de carga (60 s);
JSON, métricas CloudWatch, tabla comparativa, conclusión y decisión de
arquitectura (90 s). Explicar con palabras propias.

## Resultados

Copiar los valores observados a [RESULTADOS.md](./RESULTADOS.md). No concluir que
una táctica cumple si los percentiles pasan pero hay errores o iteraciones
descartadas. Ejecutar al menos tres repeticiones por configuración antes de
tomar una decisión final.
