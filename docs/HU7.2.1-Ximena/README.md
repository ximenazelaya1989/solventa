# EXP-006 · H7.2.1 · Disponibilidad del desembolso ante falla de Pagos o de su base de datos

Experimento de Ximena Zelaya (Grupo 7). Todo lo del experimento está en esta carpeta; el código vive en `services/pagos`, `services/siniestros` y `services/pasarela-mock`.

## Qué se prueba

**Decisión bajo prueba:** Pagos con redundancia activa (2 réplicas en ECS Fargate, una por zona, detrás de un ALB interno con health checks), datos en Aurora PostgreSQL con réplica en otra zona y conmutación por error, y Siniestros llamando a Pagos con reintentos con backoff exponencial y jitter, siempre con la misma llave de idempotencia (restricción `UNIQUE` en `pagos_db`).

**Hipótesis H1:** ante la caída de una réplica de Pagos o de la escritora de Aurora, a 10 TPS, la disponibilidad del desembolso es ≥ 99,99 % (órdenes completadas / enviadas), sin transacciones confirmadas perdidas, sin pagos duplicados, y la detección y la recuperación toman ≤ 60 s.

## Dónde está cada táctica en el código

| Táctica | Dónde |
|---|---|
| Reintentos con backoff exponencial + jitter (presupuesto 30 s, 3 s por intento) | `services/siniestros/src/indemnizaciones/pagos.client.ts` |
| Misma llave en cada reintento | `services/siniestros/src/indemnizaciones/indemnizaciones.service.ts` (`IND-<siniestroId>`) |
| Idempotencia: `UNIQUE` + devolver el pago existente (también ante dos réplicas a la vez) | `services/pagos/src/entities/pago.entity.ts`, `services/pagos/src/pagos/pagos.service.ts` |
| Llave reenviada a la pasarela (no paga doble si Pagos cae a mitad) | `services/pagos/src/pagos/pasarela.client.ts`, `services/pasarela-mock/server.js` |
| Fallar rápido durante el failover (timeouts del pool: conexión 2 s, consulta 5 s) | `services/pagos/src/app.module.ts` |
| `/health` sin consultar la BD (el ALB no retira ambas réplicas en el failover) | `services/pagos/src/health.controller.ts` |
| Redundancia activa, health check (5 s, umbral 2), Aurora escritora + réplica | `experimento/infra/exp006.yaml` (`PagosServicio`, `PagosTG`, `AuroraEscritora`, `AuroraReplica`) |
| Interruptor de la prueba de control | variable `RETRY_IDEMPOTENCY_ENABLED` (Siniestros y Pagos) |
| Inyección de la caída abrupta (SIGKILL) | `services/pagos/src/admin/fallas.controller.ts` |

## Contenido de la carpeta

```
README.md                 esta guía
experimento/
  infra/exp006.yaml       CloudFormation: Aurora (2 AZ), RDS de Siniestros, ECS, ALB interno y público, EC2 de carga
  scripts/                PowerShell, se corren en tu PC
    01-publicar-imagenes.ps1   build y push de las 3 imágenes a ECR
    02-desplegar.ps1           crea/actualiza la pila (-Modo tacticas | control)
    03-copiar-a-ec2.ps1        sube los scripts de carga / baja los resultados (-Traer)
    04-eliminar.ps1            borra todo para no gastar créditos
  carga/                  se corren en la EC2 de carga
    ejecutar_corrida.sh        una corrida completa (vacía tablas, sonda, k6, fallas, verificación, análisis)
    carga.js                   k6: 10.000 órdenes a 10 TPS
    sonda.py                   escribe en Aurora cada 200 ms (detección/recuperación del failover)
    inyectar_fallas.sh         min 5: caída de una réplica de Pagos · min 10: failover de Aurora
    verificar.py               pérdidas, duplicados y pagos huérfanos (cruza siniestros_db con pagos_db)
    obtener_logs.sh            eventos de Siniestros y Pagos desde CloudWatch
    analizar.py                resumen.md, resumen.json y grafica.png de la corrida
    comparar.py                tabla y gráfica comparativa de todas las corridas
  local/                  ensayo en tu PC con Docker (sin gastar créditos)
resultados/               aquí quedan las corridas y el PDF de resultados y análisis
```

## Paso 0 · Ensayo local (opcional, recomendado)

Con Docker Desktop abierto:

```powershell
cd docs\HU7.2.1-Ximena\experimento\local
docker compose up -d --build
curl.exe -X POST localhost:19004/siniestros/indemnizaciones -H "content-type: application/json" -d "{\"monto\":1000}"
# derribar una réplica de Pagos (el balanceador la saca y Siniestros reintenta en la otra):
curl.exe -X POST localhost:19031/admin/fallas/caida -H "x-fault-token: secreto"
docker compose down -v
```

## Paso 1 · Preparar credenciales

1. En el Learner Lab: **Start Lab**, esperar el punto verde.
2. **AWS Details → AWS CLI → Show**: copiar el bloque en `C:\Users\ximen\.aws\credentials`.
3. **AWS Details → Download PEM**: guardar `labsuser.pem` (por ejemplo en Descargas).

## Paso 2 · Publicar las imágenes (Docker Desktop abierto)

```powershell
cd docs\HU7.2.1-Ximena\experimento\scripts
.\01-publicar-imagenes.ps1
```

## Paso 3 · Desplegar (≈ 20 min, la mayor parte es Aurora)

```powershell
.\02-desplegar.ps1 -DbPassword "ClaveExp006Segura"
```

Al terminar muestra las salidas (URL de Siniestros, endpoint de Aurora, IP de la EC2). En la consola de ECS verifica que `pagos` tenga **2 tareas RUNNING** (una por zona) y que `siniestros` y `pasarela` estén RUNNING. Si PowerShell bloquea los scripts: `Set-ExecutionPolicy -Scope Process Bypass`.

## Paso 4 · Subir los scripts a la EC2 y entrar

```powershell
.\03-copiar-a-ec2.ps1 -Llave C:\Users\ximen\Downloads\labsuser.pem
ssh -i C:\Users\ximen\Downloads\labsuser.pem ec2-user@<CargaIpPublica>
```

## Paso 5 · Smoke test y piloto (en la EC2)

```bash
cd ~/carga
curl -s -X POST $SINIESTROS_URL/siniestros/indemnizaciones -H 'content-type: application/json' -d '{"monto":1000}'
TPS=1 DURACION=60s T_PAGOS=20 T_AURORA=40 ./ejecutar_corrida.sh piloto
```

El piloto dura ~2 min, inyecta las dos fallas y deja `~/resultados/piloto/resumen.md`. Sirve para revisar que todo funcione antes de las corridas largas.

## Paso 6 · Corridas con tácticas (3 × ~18 min)

```bash
./ejecutar_corrida.sh tacticas-1
./ejecutar_corrida.sh tacticas-2
./ejecutar_corrida.sh tacticas-3
```

Entre corridas el script vacía las tablas y espera 30 s; antes de lanzar la siguiente, revisa en la consola que haya otra vez 2 tareas de Pagos *healthy* y que las 2 instancias de Aurora estén *Disponibles*.

## Paso 7 · Prueba de control (3 × ~18 min)

En tu PC:

```powershell
.\02-desplegar.ps1 -DbPassword "ClaveExp006Segura" -Modo control
```

Solo actualiza las tareas de ECS (`RETRY_IDEMPOTENCY_ENABLED=false`). Cuando las nuevas tareas estén RUNNING, en la EC2:

```bash
./ejecutar_corrida.sh control-1
./ejecutar_corrida.sh control-2
./ejecutar_corrida.sh control-3
python3 comparar.py ~/resultados
```

## Paso 8 · Traer resultados y apagar todo

```powershell
.\03-copiar-a-ec2.ps1 -Llave C:\Users\ximen\Downloads\labsuser.pem -Traer
.\04-eliminar.ps1
```

Los resultados quedan en `docs/HU7.2.1-Ximena/resultados/<corrida>/`: `resumen.md`, `grafica.png`, `k6-resumen.json`, `verificacion.json`, `sonda.csv`, `inyecciones.csv` y los eventos de CloudWatch. Con eso se arma el PDF de resultados y análisis (va en `resultados/`).

## Qué mide cada cosa

| Variable | Cómo se obtiene |
|---|---|
| Disponibilidad | k6: órdenes con 201 / órdenes enviadas (`k6.csv`) |
| Transacciones confirmadas perdidas | siniestros `PAGADO` sin pago `procesado` en `pagos_db` (`verificar.py`) |
| Pagos duplicados | siniestros con más de un pago en `pagos_db` (`verificar.py`) |
| Pagos huérfanos | pagos procesados cuyo siniestro no recibió la confirmación (`verificar.py`) |
| Detección / recuperación, caída de Pagos | t0 = inyección · t1 = primer error en Siniestros · t2 = primera orden completada por reintento (CloudWatch) |
| Detección / recuperación, failover Aurora | t0 = inyección · t1 = primera escritura fallida de la sonda · t2 = primera escritura exitosa (`sonda.csv`) |

Todos los tiempos salen de relojes sincronizados por Amazon Time Sync (EC2 y tareas de Fargate), con precisión de ±0,2 s.

## Costo aproximado

Con todo encendido, unos USD 0,30-0,40 por hora (Aurora 2 × db.t3.medium es la mayor parte). Despliegue + piloto + 6 corridas caben en 3-4 horas. **Corre `04-eliminar.ps1` al terminar cada sesión.**

## Nota de seguridad

La clave de la base viaja como parámetro y variable de entorno de las tareas por simplicidad del laboratorio. En producción iría en AWS Secrets Manager.
