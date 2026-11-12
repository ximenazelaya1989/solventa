# EXP-009 · Scripts del experimento (HU10.1.3)

Disponibilidad de la cotización ante la caída de Open Finance. Hipótesis y diseño: ver el experimento en Hélix.

| Archivo | Para qué |
|---|---|
| `preparar_datos.py` | Crea los 1.000 clientes de prueba y calienta la caché de los 800 primeros |
| `locustfile.py` | Prueba de carga a 10 TPS en tres fases; tumba y restaura el mock de Open Finance |
| `analizar.py` | Calcula disponibilidad, p95/p99, tiempo de detección y recuperación, % caché vs. perfil por defecto |

## Configuraciones

Se controlan con variables de entorno de Perfilamiento (en local, antes de `docker compose up -d perfilamiento`):

| | `OPEN_FINANCE_ENABLED` | `CIRCUIT_BREAKER_ENABLED` |
|---|---|---|
| **A** línea base (solo timeout de 120 ms) | `true` | `false` |
| **B** con tácticas | `true` | `true` |

Para la cadena completa a 200 ms, Cotización lleva `PERFILAMIENTO_TIMEOUT_S=0.2`.

## Detalles de la carga

- **10 TPS repartidos:** 10 usuarios, cada uno con exactamente 1 petición por segundo y desfasados entre sí (sin ráfagas).
- **Calentamiento previo (no se mide):** 30 peticiones antes de empezar, para abrir las conexiones entre servicios. Sin él, las
  primeras peticiones simultáneas superan los 120 ms del timeout por abrir conexiones nuevas, no por las tácticas.
- **Referencia de tiempos:** `analizar.py` toma el instante de la falla y de la restauración del propio mock, que está en el mismo
  tipo de reloj que las transiciones del circuito. Con varias tareas de Perfilamiento, el tiempo de detección y el de recuperación
  son los de la **última** tarea.
- **Recuperación:** depende del momento del ciclo del circuito (abierto 30 s) en que se restaura Open Finance; puede ir de ~0 a ~35 s.

## Una corrida (local)

```bash
pip install -r requirements.txt

# 1. Configuración (ejemplo: B)
OPEN_FINANCE_ENABLED=true CIRCUIT_BREAKER_ENABLED=true PERFILAMIENTO_TIMEOUT_S=0.2 \
  docker compose up -d perfilamiento cotizacion

# 2. Datos (borra la caché anterior y la calienta)
python preparar_datos.py --perf http://localhost:18002 --redis redis://localhost:16379/0

# 3. Carga (20 min). Para una prueba rápida: FASE1_S=20 FASE2_S=40 FASE3_S=45
SALIDA=resultados/B1 MODO_FALLA=error503 \
  locust -f locustfile.py --headless --host http://localhost:18080 -u 10 -r 10

# 4. Métricas
python analizar.py resultados/B1
```

Corridas previstas: **B con `error503`**, **B con `lento2s`** y **A con `error503`**. Entre corridas hay que
volver a ejecutar el paso 2 con `--redis` (si no, la caché de la corrida anterior contamina la siguiente).

## En AWS

Las URL cambian (`--host`, `MOCK_URL`, `PERF_ADMIN_URLS`) y se corre desde una EC2 en la misma VPC.
