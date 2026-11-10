# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Solventa: caso ISIS-2212 (aseguradora digital embebida). Esta rama (`Solventa_Microservicios`) es el **sprint de microservicios**: el monolito modular de la fase anterior fue reemplazado por servicios independientes en `services/`, cada uno con su Dockerfile y su base de datos propia. El codigo del monolito sigue en el historial de git (commit `58db4e1`).

Cada integrante implementa **su propio experimento** (EXP-006 a EXP-010) sobre estos servicios y deja la evidencia en `docs/<HU>-<Nombre>/` (PDF de resultados y analisis como minimo). Los servicios son una **base compartida minima**: `/health`, BD y entidades; la logica y las tacticas de cada experimento las agrega cada quien en el servicio que necesite, detras de flags de entorno.

## Servicios

| Carpeta | Stack | BD | Puerto local | Notas |
|---|---|---|---|---|
| `services/api-gateway` | NestJS | — | 18080 | Punto de entrada. `POST /v1/cotizaciones` reenvia a Cotizacion. Sin JWT ni cuota todavia (EXP-010 / EXP-008). |
| `services/cotizacion` | FastAPI | `cotizacion_db` | 18001 | `POST /cotizaciones`: prima = prima del producto x (1 + (100 - score)/200), score desde Perfilamiento por REST. |
| `services/perfilamiento` | FastAPI | `perfilamiento_db` (+ Redis) | 18002 | `GET /perfiles/{clienteId}`, `POST /perfiles`. Sin Open Finance, breaker ni cache todavia (EXP-009). |
| `services/pagos` | NestJS | `pagos_db` | 18003 | Entidad `Pago` (llave de idempotencia unica). EXP-006. |
| `services/siniestros` | NestJS | `siniestros_db` | 18004 | `Siniestro` (herencia de tabla unica) + `Perito`. EXP-006. |
| `services/consentimiento` | NestJS | `consentimiento_db` | 18005 | Entidad `Consentimiento`. Stack por confirmar con su dueño (EXP-007). |
| `services/distribucion-socios` | NestJS | `socios_db` | 18006 | `SocioDistribucion` (`apiKey`: dato sensible). |
| `services/suscripcion-polizas` | NestJS | `suscripcion_db` | 18007 | `Suscripcion` + `Poliza` (`@VersionColumn`). Ya no hay emision atomica con Pagos: cruza servicios. |
| `services/fraude-reportes` | NestJS | `fraude_db` | 18008 | Fraude, reportes regulatorios y reaseguro. |

Identidad/KYC es Amazon Cognito (externo): no hay servicio propio. Datos demo: cliente `11111111-1111-1111-1111-111111111111` (score 70) y producto `22222222-2222-2222-2222-222222222222` (prima 150).

Cada servicio NestJS es un proyecto independiente (`package.json`, `tsconfig.json`, `nest-cli.json` propios) que carga sus entidades desde `src/entities/*.entity.ts`. No hay `package.json` en la raiz.

## Commands

```bash
docker compose up -d --build        # postgres + redis + los 9 servicios
docker compose ps
curl http://localhost:18080/health   # gateway (cada servicio: /health en su puerto)
curl -X POST http://localhost:18080/v1/cotizaciones -H 'content-type: application/json' \
  -d '{"clienteId":"11111111-1111-1111-1111-111111111111","productoId":"22222222-2222-2222-2222-222222222222"}'
docker compose logs -f <servicio>
docker compose down -v               # borra tambien los datos
```

Postgres local en `localhost:15432` (usuario/clave `postgres`), Redis en `16379`. Los puertos publicados estan en el rango 18xxx para no chocar con otros proyectos locales; entre contenedores se usan los nombres de servicio y los puertos internos (3000 NestJS, 8000 FastAPI). Una sola instancia de Postgres aloja una BD logica por servicio (`infra/postgres/init-databases.sql`); en AWS cada experimento usa su propia BD. Para un servicio NestJS suelto: `cd services/<servicio> && npm install && npm run start:dev` (necesita las variables de `.env.example`). Para FastAPI: `pip install -r requirements.txt && uvicorn app.main:app --port 8000` dentro de la carpeta del servicio.

## Conventions

- Nombres de entidades, tablas y enums en español, acorde al dominio.
- Las entidades se referencian entre servicios por `uuid` simple (`clienteId`, `polizaId`, ...), nunca con relaciones TypeORM entre servicios. Solo `Poliza` ↔ `Suscripcion` (mismo servicio) tiene `@OneToOne`.
- Liveness `/health` **sin consultar BD ni dependencias**: es una tactica de EXP-006 (el ALB no debe retirar replicas por una caida de la BD) y de EXP-009 (readiness de Perfilamiento solo verifica Redis).
- Flags de los experimentos (apagados por defecto): `RATE_LIMIT_ENABLED`, `JWT_VALIDATION_ENABLED`, `CIRCUIT_BREAKER_ENABLED`, `CONSENT_CHECK_ENABLED`, `RETRY_IDEMPOTENCY_ENABLED`.
- Prettier: comillas simples y comas finales (`.prettierrc`). `strictPropertyInitialization` desactivado: columnas con `!`.
- Columnas de dinero: `numeric` + `numericTransformer` (`services/pagos/src/common/numeric.transformer.ts`), no `float`.
- Cada servicio debe poder construirse y desplegarse **solo desde su carpeta** (cada experimento corre en la cuenta de AWS de su dueño).

## Experimentos (docs/)

Una subcarpeta por experimento; el PDF de resultados y analisis va dentro de ella. Los nombres no cambian: `HU10.1.3-Giovanna` (EXP-009), `HU7.2.1-Ximena` (EXP-006), `HU5.1.2-Daniela` (EXP-008), `HU5.1.1-Génesis` (EXP-010), `HU3.2.1-Diego` (EXP-007).

## Nota sobre el contexto de negocio

Las rutas `src/<modulo>` y los nombres de modulo citados en la seccion siguiente describen el monolito anterior; hoy cada capacidad vive en el servicio equivalente de la tabla de arriba.

## Historias de usuario y atributos de calidad (contexto de negocio)

Solventa es un caso de arquitectura de software: cada módulo de dominio de este backend implementa una o más Historias de Usuario (HU) organizadas en 10 épicas, cada una con un escenario de calidad (atributo, estímulo, medida objetivo). Úsalas para justificar decisiones de diseño (qué campos persistir, qué garantías de idempotencia/disponibilidad implementar) y para saber a qué HU responde cada entidad existente.

Notación: **(del caso, §X)** = valor con respaldo directo en el documento del caso de negocio, prioritario si hay que sustentarlo; **(propuesto)** = estimación razonable, ajustable por el equipo; **N/A** = historia de proceso arquitectónico sin escenario de calidad cuantitativo (se documenta como decisión/restricción, no como SLA).

**E1. Cotización embebida y pricing en tiempo real**
- HU1.1.1 — Socio de distribución solicita cotización vía API en horario pico → Latencia p95≤0.25s, p99≤0.5s (del caso, §6.1)
- HU1.1.2 — Actuaría versiona reglas de rating sin desplegar todo el sistema → Disponibilidad: cero downtime, rollback ≤5min (propuesto)
- HU1.1.3 — Cliente recibe precio aun si una fuente externa está lenta → Latencia: no excede p95≤0.25s vía caché/valor por defecto (del caso, §6.1)
- HU1.2.1 — Cliente/socio consulta estado de póliza o cotización → Latencia p95≤0.15s, p99≤0.3s (del caso, §6.1) — cubierta por la entidad `Poliza` existente en `src/polizas`; falta el service/controller de consulta
- HU1.3.1 — CTO: el motor de cotización escala ante campañas de socios → Escalabilidad: 500→50.000 cotizaciones/min, autoescalado ≤60s (del caso, §6.2)

**E2. Suscripción y emisión automatizada**
- HU2.1.1 — Cliente: aprobación automática si cumple el perfil de riesgo → Latencia: decisión+emisión p95≤1.5s, p99≤3s (del caso, §6.1)
- HU2.1.2 — Actuaría/Riesgo: casos límite se enrutan a revisión asistida → Disponibilidad del journey ≥99.97%; SLA de revisión ≤24h (propuesto)
- HU2.2.1 — Cliente: póliza firmada electrónicamente → Seguridad: 100% firma no repudiable y trazabilidad (propuesto)
- HU2.2.2 — Cumplimiento/legal: decisión de suscripción reconstruible → Seguridad: trazable/reconstruible 100% (del caso, §6.4)
- HU2.3.1 — Operaciones: la emisión de pólizas es idempotente → Disponibilidad ≥99.99%, cero pérdida/duplicación de transacciones confirmadas (del caso, §6.3) — relevante para `Poliza`/`Subscripcion`

**E3. Identidad, consentimiento y KYC**
- HU3.1.1 — Cliente nuevo verifica identidad en línea (KYC/AML externo) → Latencia ≤120ms/dependencia, timeout duro 700ms (del caso, §6.1)
- HU3.2.1 — Cliente otorga/revoca consentimiento de datos financieros → Seguridad: revocación efectiva ≤5min, auditable (del caso, §6.4) — entidad `Consentimiento` en `src/identidad`
- HU3.2.2 — CISO: acceso a datos consentidos por mínimo privilegio → Seguridad: 100% accesos con control de scope y auditoría (propuesto)
- HU3.3.1 — CISO: datos personales/financieros cifrados en tránsito y reposo (habeas data, PCI-DSS) → Seguridad: 100% cifrado, PII tokenizado (del caso, §6.4)

**E4. Perfilamiento y personalización con Open Data**
- HU4.1.1 — Cliente de crédito hipotecario recibe oferta de seguro de vida en el mismo flujo → Latencia p95≤0.4s, p99≤0.8s (del caso, §6.1)
- HU4.1.2 — Actuaría: perfilamiento explicable combinando Open Finance/Open Data → Seguridad: trazable/reconstruible 100% con linaje del dato (del caso, §6.4) — entidad `PerfilRiesgo.señalesOpenFinance` en `src/perfilamiento`
- HU4.2.1 — CISO: perfilamiento usa solo datos estrictamente necesarios → Seguridad: 100% campos justificados, analítica anonimizada (del caso, §6.4)
- HU4.3.1 — Actuaría: recálculo batch de perfiles al incorporar nuevas fuentes → Escalabilidad: ≥10M perfiles en <2h sin afectar el canal en línea (del caso, §6.2)

**E5. Distribución y ecosistema de socios (embedded)**
- HU5.1.1 — Socio se autentica de forma segura contra la API → Seguridad: 100% autenticación+autorización por scope, rotación de credenciales (del caso, §6.4) — entidad `SocioDistribucion.apiKey` en `src/cotizacion`
- HU5.1.2 — CTO: aislar carga y cuotas por socio → Escalabilidad: cero degradación cruzada, cuotas al 100% (propuesto)
- HU5.2.1 — Producto: onboarding de socios (5→50) sin degradar el servicio → Escalabilidad: sin degradación, aislamiento de carga (del caso, §6.2)
- HU5.3.1 — CEO: habilitar país nuevo reutilizando el núcleo → Escalabilidad: onboarding de país ≤4 semanas (del caso, §6.2)

**E6. Gestión de siniestros** (módulo `src/siniestros`)
- HU6.1.1 — Cliente reporta un siniestro y consulta su estado → Disponibilidad ≥99.97% mensual (del caso, §6.3) — `Siniestro.estado`, `fechaReporte`
- HU6.1.2 — Operaciones enruta siniestros complejos a un perito → asignación trazable 100%, disponibilidad ≥99.97% (propuesto) — `Siniestro.peritoId`/`fechaEnrutamiento`, entidad `Perito`
- HU6.2.1 — Cliente con seguro paramétrico recibe pago automático al ocurrir el evento → Escalabilidad: absorber ≥1M eventos en 10min sin pérdida (del caso, §6.2) — `Siniestro.tipo=PARAMETRICO`, `datosEventoParametrico`
- HU6.2.2 — CFO: pagos paramétricos automáticos idempotentes y auditables → Disponibilidad ≥99.99%, cero pérdida/duplicación (del caso, §6.3) — `Siniestro.claveIdempotenciaPago`, módulo `pagos`/`Desembolso`
- HU6.3.1 — Analítica/fraude detecta patrones anómalos en siniestros simulados → Seguridad: detección/bloqueo ≤1s (del caso, §6.4)

**E7. Cobros, pagos y recaudo** (módulo `src/pagos`)
- HU7.1.1 — Cliente: cobro automático de la prima al emitir la póliza → Seguridad: 100% conforme PCI-DSS, idempotencia con reintentos/backoff (del caso, §4)
- HU7.2.1 — Cliente recibe la indemnización sin demoras ni pérdidas de transacción → Disponibilidad ≥99.99%, cero pérdida de transacciones confirmadas (del caso, §6.3) — entidad `Desembolso`
- HU7.3.1 — CFO concilia cobros/pagos contra las pasarelas → Seguridad: 100% discrepancias detectadas/alertadas, proceso auditable (propuesto)

**E8. Gestión del ciclo de vida de la póliza**
- HU8.1.1 — Cliente modifica/renueva su póliza en línea → Latencia p95≤1.0s, p99≤2.0s (propuesto)
- HU8.2.1 — Cliente cancela su póliza → Seguridad: 100% cancelación procesada y auditable, efecto inmediato en cobros futuros (propuesto)
- HU8.3.1 — Cumplimiento/legal genera reportes periódicos para el regulador → Seguridad: 100% exactos y conciliados, formato ACORD (propuesto)
- HU8.3.2 — Reaseguradora recibe datos de cartera/siniestralidad estandarizados → Escalabilidad: volumen y exactitud validados 100% (propuesto) — entidades `Reaseguradora`/`ReporteReaseguro` en `src/pagos`

**E9. Analítica, fraude y cumplimiento**
- HU9.1.1 — Actuaría monitorea modelos de riesgo en producción → Disponibilidad del dashboard ≥99.9%, alertas ≤5min tras desviación (propuesto)
- HU9.2.1 — Regulador solicita justificación de una decisión de precio/suscripción → Seguridad: trazable/reconstruible 100% (del caso, §6.4)

**E10. Plataforma, resiliencia y evolución arquitectónica**
- HU10.1.1 — SRE: recuperación ante caída de una zona de disponibilidad → RTO≤10min, RPO≤30s (del caso, §6.3)
- HU10.1.2 — SRE: failover multi-región ante pérdida de una región completa → RTO≤5min, sin pérdida de transacciones confirmadas (del caso, §6.3)
- HU10.1.3 — SRE: caída de una dependencia externa no detiene la venta → Disponibilidad del journey ≥99.9%, venta continúa con perfil en caché (del caso, §6.3)
- HU10.2.1 — Equipo de desarrollo despliega varias veces al día sin downtime → cero downtime; falla de módulo no crítico no detiene venta ni pago de siniestros (del caso, §6.3)
- HU10.3.1 — Arquitecto delimita los módulos del monolito por capacidades de negocio → N/A (decisión arquitectónica)
- HU10.3.2 — Arquitecto descompone el monolito empezando por los servicios de mayor presión de escala → Escalabilidad selectiva por servicio, sin detener la operación (propuesto)
- HU10.4.1 — Arquitecto modela el catálogo de eventos de negocio → N/A (decisión de diseño)
- HU10.4.2 — Arquitecto garantiza idempotencia y orden en el procesamiento de eventos → Disponibilidad: cero duplicación de efectos en 100% de eventos procesados (propuesto)
- HU10.5.1 — Arquitecto diseña experimentos de arquitectura (carga/caos/spikes) → N/A (se gestiona como Experimentos, no como escenario de calidad)
- HU10.5.2 — SRE: trazabilidad/observabilidad extremo a extremo en un sistema orientado a eventos → Disponibilidad: correlación de trazas 100% en journeys críticos (propuesto)
