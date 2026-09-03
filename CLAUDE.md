# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Solventa backend: a NestJS + TypeORM (PostgreSQL, via `pg`) API. Currently the codebase is a domain-model scaffold — entities and modules exist for an insurance quoting/policy pipeline, but there is no `TypeOrmModule.forRoot(...)` connection config yet, no controllers/services beyond the default `AppController`/`AppService`, and `AppModule` does not import any of the four domain modules (`IdentidadModule`, `PerfilamientoModule`, `CotizacionModule`, `PolizasModule`). Wiring these up is likely upcoming work — check `src/app.module.ts` before assuming a module is active.

## Commands

```bash
npm run start:dev      # run with watch mode
npm run start:debug     # run with --inspect and watch mode
npm run build            # nest build
npm run lint              # oxlint src/ test/
npm run format           # prettier --write src/**/*.ts test/**/*.ts

npm run test              # unit tests (*.spec.ts across src/)
npm run test:watch
npm run test:cov
npm run test:e2e         # e2e tests, config in test/jest-e2e.json
npx jest path/to/file.spec.ts              # run a single test file
npx jest -t "test name pattern"            # run tests matching a name
```

There is no `.env` file and no ORM config module in the repo yet — a database connection must be provisioned (e.g. `TypeOrmModule.forRoot`) before entities can actually be persisted.

## Architecture

Code is organized as domain modules under `src/`, one directory per bounded context, each holding only `entities/` and a `*.module.ts` that registers its entities via `TypeOrmModule.forFeature([...])` (no controllers/services/DTOs yet):

- **`identidad/`** — `Cliente` (id, nombre, documentoIdentidad) and `Consentimiento` (Open Finance-style data-sharing consent, with `estado: activo | revocado` via `EstadoConsentimiento` enum), linked to a client by a plain `clienteId` uuid column.
- **`perfilamiento/`** — `PerfilRiesgo`: a risk score plus a `señalesOpenFinance` jsonb blob, linked to a client via `clienteId`.
- **`cotizacion/`** — `Cotizacion` (quote: prima, clienteId, productoId, optional socioDistribucionId), `Producto` (product catalog, id + prima), `SocioDistribucion` (distribution partner with a `canal` and `apiKey` — treat `apiKey` as sensitive).
- **`polizas/`** — `Poliza` (policy: `estado` via `EstadoPoliza` enum — pendiente/emitida/renovada/cancelada — plus clienteId, cotizacionId, productoId) and `Subscripcion` (underwriting decision), related via a real TypeORM `@OneToOne` relation (`Poliza.subscripcion` ↔ `Subscripcion.poliza`, cascading from Poliza).

**Cross-entity linking pattern:** entities reference each other almost exclusively by bare `uuid` columns (`clienteId`, `productoId`, `cotizacionId`, etc.) rather than TypeORM `@ManyToOne`/`@OneToMany` relations — the `Poliza`↔`Subscripcion` `@OneToOne` pair is the sole exception. Follow this convention (plain FK columns, not decorated relations) when adding entities unless there's a specific reason to eagerly join.

There are no cross-module imports between the four domain modules — each only registers its own entities. If you add services that need to read across domains (e.g. `Cotizacion` needing a `Cliente`), you'll need to explicitly wire that up (import the other module, inject its repository, etc.) since it doesn't exist yet.

## Conventions

- Entity names, table names (`@Entity('...')`), and enum values are in Spanish, matching the business domain; keep new domain code consistent with this.
- Prettier: single quotes, trailing commas everywhere (`.prettierrc`).
- oxlint is the configured linter (`oxlint.json`) — `@typescript-eslint/no-explicit-any` is disabled project-wide; `no-floating-promises` is a warning, not an error.
- `strictPropertyInitialization` is disabled in `tsconfig.json`, which is why entity fields use definite-assignment assertions (`id!: string`) instead of constructor initialization — keep using `!` on TypeORM entity columns rather than making them optional or adding constructors.

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
