# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Solventa backend: a NestJS + TypeORM (PostgreSQL, via `pg`) API for the ISIS-2212 course case (embedded insurance quoting/policy/claims pipeline). The codebase is organized as **12 domain modules** under `src/`, plus **2 entry points**: `src/main.ts` (the HTTP API / Fachada) and `src/batch.ts` (scheduled jobs, via `JobsModule`).

This is a shared scaffold: outside of `suscripcion`, `polizas` and `pagos` (which implement the real atomic-emission/idempotency/optimistic-locking logic described below), most service methods are **just signatures** with `// TODO(<modulo>): implementar por el dueño del modulo` — each team builds their own experiment on top of this base. See "TODO por módulo" at the end of this file before assuming a method does anything.

## Commands

```bash
npm run start:dev          # API with watch mode, listens on 0.0.0.0:$PORT (default 3000)
npm run start:debug        # API with --inspect and watch mode
npm run build               # nest build (compiles all of src/, including main.ts and batch.ts)
npm run start:batch         # runs dist/batch.js (build first) — recalculo de perfiles, cesiones, reportes
npm run migration:generate -- src/migrations/NombreMigracion   # via src/config/data-source.ts
npm run migration:run
npm run lint                 # oxlint src/ test/
npm run format               # prettier --write src/**/*.ts test/**/*.ts

npm run test              # unit tests (*.spec.ts across src/)
npm run test:watch
npm run test:cov
npm run test:e2e         # e2e tests, config in test/jest-e2e.json
npx jest path/to/file.spec.ts              # run a single test file
npx jest -t "test name pattern"            # run tests matching a name

docker compose up -d --build   # postgres:16 + 2 replicas de la API (api1/api2) + nginx en :8080
```

Copy `.env.example` to `.env` first. `DB_SYNCHRONIZE` controls `TypeOrmModule.forRoot`'s `synchronize` option (default `false` — set to `true` for local/dev schema creation); in anything resembling production use the migrations in `src/config/data-source.ts` instead.

> **Si ya tenías el volumen `solventa-db-data` de antes de este refactor** (por ejemplo de pruebas manuales previas), bájalo y bórralo antes de levantar de nuevo: `docker compose down -v`. `synchronize` no migra filas existentes — por ejemplo, agregar `Poliza.version` como `@VersionColumn()` (`NOT NULL`) falla con `column "version" of relation "polizas" contains null values` si la tabla `polizas` ya tenía filas de antes. Para no perder datos reales, usa `migration:generate`/`migration:run` en vez de `synchronize`.

## Architecture

### The 12 modules

Each module directory normally has `entities/`, `<modulo>.service.ts` and `<modulo>.controller.ts`. Entities reference each other almost exclusively by bare `uuid` columns (`clienteId`, `productoId`, `cotizacionId`, etc.) rather than TypeORM relations — the `Poliza` ↔ `Suscripcion` `@OneToOne` pair (owned from the `Suscripcion` side via `polizaId`/`@JoinColumn`) is the sole exception. Follow this convention when adding entities.

1. **`identidad/`** — `Cliente`, `IdentidadCredencial` (KYC: `metodoKYC`, `estadoVerificacion`, `fechaVerificacion`). Service: `registrar`, `verificarKyc` (TODO).
2. **`consentimiento/`** — `Consentimiento` (Open Finance-style consent, `estado: activo | revocado`). Service: `tieneConsentimientoActivo(clienteId, alcance)` **implemented**; `otorgar`/`revocar`/`consultar` (TODO).
3. **`perfilamiento/`** — `PerfilRiesgo` (`clienteId` unique, 0..1 per client; `señalesOpenFinance` jsonb). Service: `obtenerScore(perfilRiesgoId)` **implemented** (used by `suscripcion`); `calcularPerfil`/`recalcularTodos` (TODO). Imports `identidad` + `consentimiento`.
4. **`cotizacion/`** — `Cotizacion` (now with `perfilRiesgoId` nullable uuid), `Producto`, `SocioDistribucion` (`apiKey` — treat as sensitive). **Not touched by this refactor** beyond `cotizacion.entity.ts` (added `perfilRiesgoId`) and `cotizacion.module.ts` (added `exports: [TypeOrmModule]`, a one-line diff) — a teammate's branch (`origin/feature/hu112-rolling-update-reglas-rating`, rating-rules engine) targets this module and hasn't merged yet.
5. **`suscripcion/`** — `Suscripcion` (renamed from `Subscripcion`; `cotizacionId` unique). The one module with real end-to-end business logic: `SuscripcionService.decidir()` — see "Concurrencia" below. Imports `cotizacion`, `perfilamiento`, `polizas`, `pagos`.
6. **`polizas/`** — `Poliza` (`@VersionColumn() version`; no `cotizacionId` — that lives on `Suscripcion`). `PolizasService.emitir(manager, dto)`, `renovar(id, version)` / `cancelar(id, version)` (409 on version mismatch).
7. **`pagos/`** — `Pago` (renamed from `Desembolso`; `tipo: cobro_prima | indemnizacion`; `estado` includes `pendiente`/`bloqueado`/`procesado`/`fallido`; `monto` is `numeric` + a transformer, see `src/common/transformers/numeric.transformer.ts`). `PagosService.cobrarPrima()`/`pagarIndemnizacion()` **implemented** (idempotent inserts); `procesar`/`conciliar` (TODO). **Never imports `polizas`** — only stores `polizaId`/`siniestroId` as plain uuids.
8. **`siniestros/`** — `Siniestro` is single-table inheritance (`@Entity` + `@TableInheritance`, discriminator column `tipo`), abstract base class, with `@ChildEntity` subclasses `SiniestroAsistido` and `SiniestroParametrico` (the latter carries `datosEventoParametrico` + `claveIdempotenciaPago`); `Perito` (now with `zona`). Service: `reportar`/`asignarPerito`/`aprobar`/`eventoParametrico` (TODO). Imports `polizas`, `pagos`, `analitica-fraude`.
9. **`analitica-fraude/`** — `MotorDeteccionFraude` (`patronDetectado`/`nivelRiesgo`/`estado` are plain `varchar` — valid values are undefined, TODO). Service: `evaluarSiniestro`/`bloquearTransaccion` (TODO). Imports `pagos`.
10. **`reaseguro/`** — `Reaseguradora` (now with `porcentajeCesion`), `CesionPoliza` (new; unique pair `polizaId`+`reaseguradoraId`). Service: `registrarCesiones` (TODO — cesiones are created in the batch, not at policy emission, per design decision). Imports `polizas`.
11. **`reporteria/`** — `ReporteRegulatorio` (renamed from `ReporteReaseguro`; `destinatario` now covers both regulator and reinsurer). Service: `generar`/`enviar` (TODO). Imports `polizas`.
12. **`integraciones/`** — the Orquestador. `OrquestadorService.llamar<T>(dependencia, fn, opciones?: { timeoutMs? })` — hard timeout **implemented** (700ms default, via `Promise.race`); retries, read-only cache fallback and a per-dependency semaphore are TODO. No mock clients (KYC/Open Finance/pasarela/regulador) exist yet.

Supporting, non-domain code: `jobs/` (`JobsModule`/`JobsService`, driven by `src/batch.ts`), `common/guards/api-key.guard.ts` (`ApiKeyGuard`, validates `x-api-key` against `SocioDistribucion` — **not wired to any controller yet**, see TODO below), `common/transformers/numeric.transformer.ts`, `config/data-source.ts` (standalone `DataSource` for the TypeORM migrations CLI).

### Allowed module dependencies (no cycles)

```
perfilamiento  -> identidad, consentimiento
suscripcion    -> cotizacion, perfilamiento, polizas, pagos
siniestros     -> polizas, pagos, analitica-fraude
analitica-fraude -> pagos
reaseguro      -> polizas
reporteria     -> polizas
pagos          -> (nothing of the above; never imports polizas)
```
Anything that calls an external system should go through `integraciones` (`OrquestadorService`) once that module has real clients.

## Concurrencia, idempotencia y versión (implemented in suscripcion/polizas/pagos)

- **Atomic emission**: `SuscripcionService.decidir()` opens `dataSource.transaction(manager => ...)` and passes the same `manager` into `PolizasService.emitir(manager, dto)` and `PagosService.cobrarPrima(manager, polizaId, monto)`. `monto` is `cotizacion.prima` — `Poliza` itself has no `prima` field. The payment gateway is never called inside this transaction (that's `PagosService.procesar()`, still TODO).
- **Suscripcion idempotency**: `Suscripcion.cotizacionId` is unique. If one already exists for that `cotizacionId`, `decidir()` returns it (`idempotente: true`) without creating anything. On a concurrent race, Postgres raises `23505`; that's caught **outside** the `dataSource.transaction()` callback (TypeORM has already rolled back by the time the promise rejects), and the winning row is re-read and returned.
- **Pago idempotency**: `Pago.claveIdempotencia` is unique; `cobrarPrima`/`pagarIndemnizacion` insert via `ON CONFLICT DO NOTHING` with keys `prima:{polizaId}` / `indem:{siniestroId}`. (`SiniestroParametrico.claveIdempotenciaPago` is a separate field that records the triggering external event's key — it is not what enforces uniqueness at the DB level; `Pago.claveIdempotencia` is.)
- **Optimistic version on Poliza**: `Poliza.version` (`@VersionColumn()`); `renovar(id, version)`/`cancelar(id, version)` compare the caller-supplied version against the persisted one and throw `ConflictException` (409) on mismatch.
- **Connection pool**: `extra.max = DB_POOL_MAX` (default 10) in `TypeOrmModule.forRoot` (`src/app.module.ts`).

## Conventions

- Entity names, table names (`@Entity('...')`), and enum values are in Spanish, matching the business domain; keep new domain code consistent with this.
- Prettier: single quotes, trailing commas everywhere (`.prettierrc`).
- oxlint is the configured linter (`oxlint.json`) — `@typescript-eslint/no-explicit-any` is disabled project-wide; `no-floating-promises` is a warning, not an error.
- `strictPropertyInitialization` is disabled in `tsconfig.json`, which is why entity fields use definite-assignment assertions (`id!: string`) instead of constructor initialization — keep using `!` on TypeORM entity columns rather than making them optional or adding constructors.
- Money columns use `type: 'numeric'` + `numericTransformer` (not `float`) so they read back as `number`, not `string` — see `src/common/transformers/numeric.transformer.ts` and `Pago.monto`.

## TODO por módulo

- **identidad**: `registrar`, `verificarKyc` (should call the Orquestador — `src/integraciones` — with a hard 700ms timeout once its clients exist).
- **consentimiento**: `otorgar`, `revocar` (efectiva ≤5min, HU3.2.1), `consultar`.
- **perfilamiento**: `calcularPerfil` (only when `consentimientoService.tieneConsentimientoActivo(...)` is true; score formula undefined), `recalcularTodos` (batch job, HU4.3.1).
- **cotizacion**: entirely owned by whoever lands `origin/feature/hu112-rolling-update-reglas-rating` — solicitar cotización, calcular prima, caché de productos, motor de reglas de rating.
- **suscripcion**: `SUSCRIPCION_UMBRAL_APROBACION`/`SUSCRIPCION_UMBRAL_REVISION` are still hardcoded consts (`UMBRAL_APROBADO`/`UMBRAL_REVISION_ASISTIDA` in `suscripcion.service.ts`), not env-configurable yet; the controller doesn't yet shape the `201`/`404`/`idempotente`/`polizaId` response contract; `GET /suscripciones/:id` is missing.
- **polizas**: no controller endpoints yet (`GET /polizas/:id`, and HTTP wiring for `renovar`/`cancelar`).
- **pagos**: `procesar()` (actual pasarela call, outside the emission transaction), `conciliar()`.
- **siniestros**: `reportar`, `asignarPerito`, `aprobar`, `eventoParametrico`.
- **analitica-fraude**: `evaluarSiniestro` (must respond in <1s, HU6.3.1), `bloquearTransaccion`; also undefined: valid values for `MotorDeteccionFraude.patronDetectado`/`nivelRiesgo`/`estado`.
- **reaseguro**: `registrarCesiones` (runs from the batch, not at policy emission).
- **reporteria**: `generar`, `enviar`.
- **integraciones**: retries with backoff, read-only cache fallback, per-dependency semaphore (env-configurable limit) in `OrquestadorService.llamar()`; mock clients for KYC, Open Finance, payment gateway and regulator.
- **plataforma/común**: `ApiKeyGuard` (`src/common/guards/api-key.guard.ts`) and `ThrottlerGuard` (configured via `ThrottlerModule.forRoot` in `src/app.module.ts`, env vars `THROTTLE_TTL_MS`/`THROTTLE_LIMIT_POR_SOCIO`) are not applied to any controller yet — wire them onto partner-facing endpoints (HU5.1.1/HU5.1.2) when those exist. Explicitly **not** applied to anything in `src/cotizacion`.

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
- HU2.3.1 — Operaciones: la emisión de pólizas es idempotente → Disponibilidad ≥99.99%, cero pérdida/duplicación de transacciones confirmadas (del caso, §6.3) — implementada en `SuscripcionService.decidir()`/`Poliza`/`Suscripcion` (ver "Concurrencia" arriba)

**E3. Identidad, consentimiento y KYC**
- HU3.1.1 — Cliente nuevo verifica identidad en línea (KYC/AML externo) → Latencia ≤120ms/dependencia, timeout duro 700ms (del caso, §6.1)
- HU3.2.1 — Cliente otorga/revoca consentimiento de datos financieros → Seguridad: revocación efectiva ≤5min, auditable (del caso, §6.4) — entidad `Consentimiento` en `src/consentimiento`
- HU3.2.2 — CISO: acceso a datos consentidos por mínimo privilegio → Seguridad: 100% accesos con control de scope y auditoría (propuesto)
- HU3.3.1 — CISO: datos personales/financieros cifrados en tránsito y reposo (habeas data, PCI-DSS) → Seguridad: 100% cifrado, PII tokenizado (del caso, §6.4)

**E4. Perfilamiento y personalización con Open Data**
- HU4.1.1 — Cliente de crédito hipotecario recibe oferta de seguro de vida en el mismo flujo → Latencia p95≤0.4s, p99≤0.8s (del caso, §6.1)
- HU4.1.2 — Actuaría: perfilamiento explicable combinando Open Finance/Open Data → Seguridad: trazable/reconstruible 100% con linaje del dato (del caso, §6.4) — entidad `PerfilRiesgo.señalesOpenFinance` en `src/perfilamiento`
- HU4.2.1 — CISO: perfilamiento usa solo datos estrictamente necesarios → Seguridad: 100% campos justificados, analítica anonimizada (del caso, §6.4)
- HU4.3.1 — Actuaría: recálculo batch de perfiles al incorporar nuevas fuentes → Escalabilidad: ≥10M perfiles en <2h sin afectar el canal en línea (del caso, §6.2)

**E5. Distribución y ecosistema de socios (embedded)**
- HU5.1.1 — Socio se autentica de forma segura contra la API → Seguridad: 100% autenticación+autorización por scope, rotación de credenciales (del caso, §6.4) — entidad `SocioDistribucion.apiKey` en `src/cotizacion`; guard en `src/common/guards/api-key.guard.ts` (no aplicado aún, ver TODO)
- HU5.1.2 — CTO: aislar carga y cuotas por socio → Escalabilidad: cero degradación cruzada, cuotas al 100% (propuesto) — `ThrottlerModule` en `src/app.module.ts` (no aplicado aún, ver TODO)
- HU5.2.1 — Producto: onboarding de socios (5→50) sin degradar el servicio → Escalabilidad: sin degradación, aislamiento de carga (del caso, §6.2)
- HU5.3.1 — CEO: habilitar país nuevo reutilizando el núcleo → Escalabilidad: onboarding de país ≤4 semanas (del caso, §6.2)

**E6. Gestión de siniestros** (módulo `src/siniestros`)
- HU6.1.1 — Cliente reporta un siniestro y consulta su estado → Disponibilidad ≥99.97% mensual (del caso, §6.3) — `Siniestro.estado`, `fechaReporte`
- HU6.1.2 — Operaciones enruta siniestros complejos a un perito → asignación trazable 100%, disponibilidad ≥99.97% (propuesto) — `Siniestro.peritoId`/`fechaEnrutamiento`, entidad `Perito`
- HU6.2.1 — Cliente con seguro paramétrico recibe pago automático al ocurrir el evento → Escalabilidad: absorber ≥1M eventos en 10min sin pérdida (del caso, §6.2) — subclase `SiniestroParametrico`, `datosEventoParametrico`
- HU6.2.2 — CFO: pagos paramétricos automáticos idempotentes y auditables → Disponibilidad ≥99.99%, cero pérdida/duplicación (del caso, §6.3) — `SiniestroParametrico.claveIdempotenciaPago` + `Pago.claveIdempotencia` (`indem:{siniestroId}`) en `src/pagos`
- HU6.3.1 — Analítica/fraude detecta patrones anómalos en siniestros simulados → Seguridad: detección/bloqueo ≤1s (del caso, §6.4)

**E7. Cobros, pagos y recaudo** (módulo `src/pagos`)
- HU7.1.1 — Cliente: cobro automático de la prima al emitir la póliza → Seguridad: 100% conforme PCI-DSS, idempotencia con reintentos/backoff (del caso, §4) — `PagosService.cobrarPrima()`, clave `prima:{polizaId}`
- HU7.2.1 — Cliente recibe la indemnización sin demoras ni pérdidas de transacción → Disponibilidad ≥99.99%, cero pérdida de transacciones confirmadas (del caso, §6.3) — entidad `Pago` (antes `Desembolso`)
- HU7.3.1 — CFO concilia cobros/pagos contra las pasarelas → Seguridad: 100% discrepancias detectadas/alertadas, proceso auditable (propuesto) — `PagosService.conciliar()` (TODO)

**E8. Gestión del ciclo de vida de la póliza**
- HU8.1.1 — Cliente modifica/renueva su póliza en línea → Latencia p95≤1.0s, p99≤2.0s (propuesto) — `PolizasService.renovar(id, version)`
- HU8.2.1 — Cliente cancela su póliza → Seguridad: 100% cancelación procesada y auditable, efecto inmediato en cobros futuros (propuesto) — `PolizasService.cancelar(id, version)`
- HU8.3.1 — Cumplimiento/legal genera reportes periódicos para el regulador → Seguridad: 100% exactos y conciliados, formato ACORD (propuesto) — `ReporteRegulatorio` en `src/reporteria`
- HU8.3.2 — Reaseguradora recibe datos de cartera/siniestralidad estandarizados → Escalabilidad: volumen y exactitud validados 100% (propuesto) — entidades `Reaseguradora`/`CesionPoliza` en `src/reaseguro`, `ReporteRegulatorio.destinatario` en `src/reporteria`

**E9. Analítica, fraude y cumplimiento**
- HU9.1.1 — Actuaría monitorea modelos de riesgo en producción → Disponibilidad del dashboard ≥99.9%, alertas ≤5min tras desviación (propuesto)
- HU9.2.1 — Regulador solicita justificación de una decisión de precio/suscripción → Seguridad: trazable/reconstruible 100% (del caso, §6.4)

**E10. Plataforma, resiliencia y evolución arquitectónica**
- HU10.1.1 — SRE: recuperación ante caída de una zona de disponibilidad → RTO≤10min, RPO≤30s (del caso, §6.3)
- HU10.1.2 — SRE: failover multi-región ante pérdida de una región completa → RTO≤5min, sin pérdida de transacciones confirmadas (del caso, §6.3)
- HU10.1.3 — SRE: caída de una dependencia externa no detiene la venta → Disponibilidad del journey ≥99.9%, venta continúa con perfil en caché (del caso, §6.3)
- HU10.2.1 — Equipo de desarrollo despliega varias veces al día sin downtime → cero downtime; falla de módulo no crítico no detiene venta ni pago de siniestros (del caso, §6.3)
- HU10.3.1 — Arquitecto delimita los módulos del monolito por capacidades de negocio → N/A (decisión arquitectónica) — ver "Los 12 módulos" arriba
- HU10.3.2 — Arquitecto descompone el monolito empezando por los servicios de mayor presión de escala → Escalabilidad selectiva por servicio, sin detener la operación (propuesto)
- HU10.4.1 — Arquitecto modela el catálogo de eventos de negocio → N/A (decisión de diseño; bus de eventos en pausa, no implementado)
- HU10.4.2 — Arquitecto garantiza idempotencia y orden en el procesamiento de eventos → Disponibilidad: cero duplicación de efectos en 100% de eventos procesados (propuesto)
- HU10.5.1 — Arquitecto diseña experimentos de arquitectura (carga/caos/spikes) → N/A (se gestiona como Experimentos, no como escenario de calidad)
- HU10.5.2 — SRE: trazabilidad/observabilidad extremo a extremo en un sistema orientado a eventos → Disponibilidad: correlación de trazas 100% en journeys críticos (propuesto)
