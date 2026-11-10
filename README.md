# Solventa — sprint de microservicios (ISIS-2212)

Aseguradora digital embebida del caso Solventa, organizada en microservicios independientes. Cada integrante del equipo ejecuta su propio experimento de arquitectura sobre estos servicios y deja la evidencia en `docs/`.

## Estructura

```
services/            un microservicio por carpeta (Dockerfile y BD propios)
  api-gateway/         NestJS    · punto de entrada
  cotizacion/          FastAPI   · cotizacion_db
  perfilamiento/       FastAPI   · perfilamiento_db (+ Redis)
  mock-open-finance/   FastAPI   · mock compartido de Open Finance (EXP-009 y EXP-007)
  pagos/               NestJS    · pagos_db
  siniestros/          NestJS    · siniestros_db
  consentimiento/      FastAPI   · consentimiento_db
  distribucion-socios/ NestJS    · socios_db
  suscripcion-polizas/ NestJS    · suscripcion_db
  fraude-reportes/     NestJS    · fraude_db
infra/postgres/      script que crea una BD por servicio (solo para uso local)
docs/                una subcarpeta por experimento, con su PDF de resultados y analisis
docker-compose.yml   levanta todo en local
```

## Levantar todo en local

Requiere Docker Desktop corriendo.

```bash
docker compose up -d --build
docker compose ps
```

| Servicio | URL local |
|---|---|
| API Gateway | http://localhost:18080 |
| Cotizacion | http://localhost:18001 |
| Perfilamiento | http://localhost:18002 |
| Mock de Open Finance | http://localhost:18009 |
| Pagos | http://localhost:18003 |
| Siniestros | http://localhost:18004 |
| Consentimiento | http://localhost:18005 |
| Distribucion y socios | http://localhost:18006 |
| Suscripcion y polizas | http://localhost:18007 |
| Fraude y reportes | http://localhost:18008 |
| Postgres / Redis | localhost:15432 / localhost:16379 |

Cada servicio expone `GET /health`.

## Prueba de humo de la cadena de cotizacion

```bash
curl -X POST http://localhost:18080/v1/cotizaciones \
  -H 'content-type: application/json' \
  -d '{"clienteId":"11111111-1111-1111-1111-111111111111","productoId":"22222222-2222-2222-2222-222222222222"}'
```

Devuelve prima `172.5` (prima del producto 150 × 1,15 por el score de riesgo 70). El gateway llama a Cotizacion y esta a Perfilamiento, cada uno con su base de datos.

## Experimentos

Los servicios son una base minima: cada experimento agrega su logica y sus tacticas en el servicio que le corresponde, detras de flags de entorno apagados por defecto. Las carpetas de `docs/` son `HU10.1.3-Giovanna`, `HU7.2.1-Ximena`, `HU5.1.2-Daniela`, `HU5.1.1-Génesis` y `HU3.2.1-Diego`.

Mas detalle (stack, notas y convenciones) en [CLAUDE.md](CLAUDE.md).
