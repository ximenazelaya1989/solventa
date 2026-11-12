# EXP-010 · HU5.1.1 · Autenticación y autorización de socios al solicitar una cotización

Experimento de Génesis Parada (Grupo 7). Todo lo del experimento está en esta carpeta. El código vive en `services/distribucion-socios` y `services/api-gateway`, y la infraestructura de AWS en `experimento/infra/exp010.yaml`.

## Qué se prueba

**Funcionalidad de negocio:** un socio de distribución pide, desde su app, una cotización para uno de sus clientes (`POST /v1/socios/cotizaciones`).

**Decisión bajo prueba: gateway en dos niveles.**

```
Socio ──► AWS API Gateway (borde) ──► api-gateway interno (NestJS) ──► Distribución y socios ──► Cotización ──► Perfilamiento
          · JWT de Cognito: 401           · exige el secreto del borde   · cliente del socio: 403
          · scope cotizaciones/crear: 403   (si falta: 403)               · si es suyo: pide la cotización
```

- La autenticación y el scope los valida un **gateway de terceros** (AWS API Gateway HTTP API con autorizador JWT de Cognito). Se **configura**, no se programa. Es la corrección de la profesora.
- El api-gateway en NestJS queda detrás, sin cambios en lo de EXP-008: solo se agrega una ruta de reenvío en un archivo propio.

**Hipótesis:** el 100 % de las peticiones indebidas se rechaza con 401/403 sin llegar a los componentes que no debe alcanzar, y el 100 % de las válidas completa el flujo con 201.

| # | Caso (20 peticiones secuenciales, sin carga) | Esperado | Quién rechaza |
|---|---|---|---|
| 1 | Sin token | 401 | AWS API Gateway |
| 2 | Token con la firma alterada | 401 | AWS API Gateway |
| 3 | Token expirado | 401 | AWS API Gateway |
| 4 | Token sin el scope `cotizaciones/crear` | 403 | AWS API Gateway |
| 5 | Socio A pide para un cliente del socio B | 403 | Distribución y socios (Cotización no recibe nada) |
| 6 | Socio A pide para su propio cliente | 201 | — (llega a Cotización → Perfilamiento) |
| extra | Llamada directa al gateway interno, saltándose el borde (5 peticiones) | 403 | api-gateway interno |

## Dónde está cada táctica (para el video)

| Táctica | Dónde |
|---|---|
| Autenticar actores (firma, emisor, vencimiento del JWT) | `experimento/infra/exp010.yaml` → `AutorizadorJwt` (AWS API Gateway) y `UserPool`, `ClienteSocio*` (Cognito, OAuth2 client_credentials) |
| Autorizar actores por scope | `exp010.yaml` → `RutaCotizacionSocio.AuthorizationScopes: [cotizaciones/crear]` y `ServidorRecursos` |
| Propagar la identidad ya validada | `exp010.yaml` → `IntegracionGatewayInterno.RequestParameters` (`x-socio-client-id` = claim `client_id`) |
| Autorizar actores por pertenencia del cliente | `services/distribucion-socios/src/exp010/socios-cotizaciones.controller.ts` + tablas `credenciales_socio` y `clientes_socio` |
| Limitar acceso (no saltarse el borde) | `services/api-gateway/src/socios-cotizaciones.controller.ts` (encabezado `x-origin-verify`) + `SecretoOrigen` en Secrets Manager |
| Cifrado en tránsito hacia la BD | `DB_SSL=true` en Distribución y `sslmode=require` en Cotización y Perfilamiento |
| Flag del experimento (apagado por defecto) | `JWT_VALIDATION_ENABLED` en api-gateway y distribucion-socios: si es `false`, la ruta nueva responde 404 |

Cotización y Perfilamiento **no se modificaron**: Distribución usa el contrato existente `POST /cotizaciones`.

## Contenido

```
README.md                     esta guía
experimento/
  infra/exp010.yaml           CloudFormation: Cognito, AWS API Gateway, ECS Fargate (4 servicios), 2 ALB, RDS, Secrets Manager
  scripts/                    bash (Mac/Linux), se corren desde esta carpeta
    01-publicar-imagenes.sh   build (linux/amd64) y push de las 4 imágenes a ECR
    02-desplegar.sh           crea/actualiza la pila (≈15 min)
    03-obtener-tokens.sh      tokens de Cognito para los casos (resultados/tokens.properties, no se sube)
    04-ejecutar-casos.sh      corrida completa: casos + bypass + logs + análisis
    05-recolectar-logs.sh     conteos de CloudWatch Logs Insights por componente
    06-eliminar.sh            borra todo para no gastar créditos
  pruebas/
    exp010.jmx                plan de JMeter con los 6 casos
    ejecutar_casos.py         alternativa sin JMeter (y modo --local)
    analizar.py               resumen.md, resumen.json y grafica.png de una corrida
resultados/                   aquí quedan las corridas y el PDF de resultados y análisis
```

## Paso 0 · Ensayo local (opcional)

En local no hay AWS API Gateway, así que solo se prueban los casos 5 y 6 y el bypass (el script simula el borde).

```bash
JWT_VALIDATION_ENABLED=true ORIGIN_VERIFY_SECRET=secreto-local docker compose up -d --build \
  postgres redis perfilamiento cotizacion distribucion-socios api-gateway
python3 docs/HU5.1.1-Génesis/experimento/pruebas/ejecutar_casos.py --local --salida /tmp/exp010-local
docker compose down -v
```

## Paso 1 · Credenciales

1. En el Learner Lab: **Start Lab** y esperar el punto verde.
2. **AWS Details → AWS CLI → Show**: copiar el bloque en `~/.aws/credentials`.
3. Tener Docker Desktop abierto y, si se quiere usar JMeter, `brew install jmeter`.

## Pasos 2 a 6 · Desplegar, correr y borrar

```bash
cd docs/HU5.1.1-Génesis/experimento/scripts
./01-publicar-imagenes.sh
./02-desplegar.sh ClaveSegura123        # solo letras y números
# esperar a que los 4 servicios de ECS estén RUNNING y healthy
./03-obtener-tokens.sh
./04-ejecutar-casos.sh                  # espera sola a que el token del caso 3 expire (5 min)
./06-eliminar.sh                        # al terminar
```

Cada corrida queda en `resultados/corrida-<fecha>/` con `resumen.md` (tabla por caso y verificación con logs), `resumen.json`, `grafica.png` y, si se usó JMeter, `reporte-jmeter/`.

**Criterio:** la hipótesis se confirma solo si el 100 % de las peticiones de cada caso recibe el código esperado **y** ninguna petición rechazada aparece en los logs de un componente que no debía alcanzar. `analizar.py` cruza ambas cosas.

## Variables controladas

- Misma infraestructura y mismos datos semilla en todas las corridas.
- Limitador de EXP-008 apagado (`RATE_LIMIT_ENABLED=false`), para que un 429 no se confunda con un 401 o 403.
- Peticiones secuenciales (1 hilo), sin carga: el ASR es de seguridad.

## Archivos compartidos que se tocaron (cambio mínimo, avisar a sus dueños)

- `services/api-gateway/src/app.module.ts`: una línea para registrar el controlador nuevo (Daniela, EXP-008, comparte el gateway).
- `services/distribucion-socios/src/app.module.ts`: registro del controlador y la semilla, y `ssl` por `DB_SSL` (mismo patrón que Pagos).
- `docker-compose.yml` y los `.env.example` de ambos servicios: solo líneas nuevas.
- Tablas nuevas en `socios_db` (`credenciales_socio`, `clientes_socio`). No se cambió ninguna tabla existente.
