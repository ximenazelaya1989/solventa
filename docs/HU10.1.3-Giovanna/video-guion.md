# EXP-009 · Guion del video (máximo 8 min)

Orden que pide la entrega: **contexto → despliegue → tácticas → ejecución**. Debe hablarse con tus propias palabras: este guion es una guía de qué mostrar y qué decir, no un texto para leer.

Si la funcionalidad o la arquitectura mostradas no corresponden al ASR/diseño, la entrega se califica sobre 2,5. Todo lo que muestres debe ser **cotización con Open Finance caído** (HU10.1.3).

| Parte | Tiempo | Acumulado |
|---|---:|---:|
| 1. Contexto | 0:45 | 0:45 |
| 2. Despliegue | 1:15 | 2:00 |
| 3. Tácticas | 2:15 | 4:15 |
| 4. Ejecución de la prueba | 3:30 | 7:45 |

## Preparación antes de grabar

- Pestañas abiertas y ordenadas: consola de AWS (ECS, ALB, RDS, ElastiCache, EC2), el código (`open_finance.py`), la terminal de la EC2 con Locust y CloudWatch Logs.
- Corrida B en marcha (ver parte 4) y una terminal lista para consultar el estado de Perfilamiento.
- Cierra pestañas con datos personales o credenciales del lab.

## 1. Contexto (0:45)

**Mostrar:** el ASR de Hélix (HU10.1.3) y la hipótesis.

**Decir:**
- Solventa vende seguros y, para dar el precio, necesita datos de un proveedor externo, Open Finance.
- El caso exige que la venta siga aunque se caiga un tercero: disponibilidad de la cotización ≥ 99,9 %.
- Hipótesis: con timeout de 120 ms, circuit breaker, bulkhead y degradación con caché o perfil por defecto, la cotización se mantiene ≥ 99,9 % con Open Finance caído, el circuito abre en ≤ 5 s y el p95 se mantiene ≤ 250 ms.
- Se prueba contra una línea base (A, sin tácticas) y la configuración con tácticas (B).

## 2. Despliegue (1:15)

**Mostrar en la consola de AWS** (con la región us-east-1 visible):
- **ECS:** el cluster con los servicios `api-gateway`, `cotizacion`, `perfilamiento` (2 tareas) y `mock-open-finance`, todos en estado activo.
- **ALB:** las reglas por ruta y los target groups *healthy*. Señalar el health check `/ready` de Perfilamiento.
- **RDS** y **ElastiCache** (Redis) en estado disponible.
- **EC2** desde donde se lanza la carga.

**Decir:** qué hace cada pieza en una frase, y que el mock de Open Finance es el que se va a tumbar durante la prueba.

## 3. Tácticas (2:15)

Para cada una: **dónde está en el código o la configuración** y **qué problema evita**. Abre `services/perfilamiento/app/open_finance.py`.

| Táctica | Mostrar | Decir (idea) |
|---|---|---|
| Timeout 120 ms | `OPEN_FINANCE_TIMEOUT_S` y la llamada `_consultar` | No esperar más del presupuesto por dependencia del caso. |
| Circuit breaker | clase `CircuitBreaker` (ventana de 10, 50 %, 30 s, 3 pruebas) | Si falla mucho, deja de llamar y evita acumular esperas. |
| Bulkhead | `BULKHEAD_MAX` y el semáforo | Máximo 10 llamadas simultáneas a Open Finance; una caída no agota todo el servicio. |
| Degradación | `_degradar`: caché en Redis y `PERFIL_POR_DEFECTO` | Si no hay datos nuevos, se usa el último perfil conocido o uno prudente. La venta sigue. |
| Readiness solo Redis | endpoint `/ready` y el health check del ALB | La caída de Open Finance no marca las tareas como no saludables. |
| Flags | `OPEN_FINANCE_ENABLED` y `CIRCUIT_BREAKER_ENABLED` en las variables del task definition | A = sin tácticas, B = con tácticas. |
| Inyección de falla | el mock y `/admin/fail` | Chaos engineering: tumbar el proveedor a propósito. |

## 4. Ejecución de la prueba (3:30)

La prueba completa dura 20 minutos; no se muestra entera. Propuesta: grabar la corrida B real y **acelerar** (o cortar) la fase normal, dejando ver en vivo la inyección de la falla. Dilo en el video ("la prueba dura 20 minutos; aquí se muestra acelerada").

**Mostrar, en este orden:**
1. Locust corriendo a 10 TPS y una cotización real devolviendo precio (funcionalidad de negocio): `POST /v1/cotizaciones` por el ALB.
2. **Se inyecta la falla** (`POST /admin/fail`) y se ve que Open Finance responde 503.
3. Las cotizaciones **siguen funcionando**: consultar `/admin/open-finance/estado` y ver el circuito en `ABIERTO` y los contadores de `servidasDesdeCache` y `servidasPerfilPorDefecto`.
4. CloudWatch Logs: las líneas `evento=CIRCUITO` y `evento=DEGRADADO`.
5. Se restaura Open Finance y el circuito pasa a `SEMIABIERTO` y luego `CERRADO`.
6. **Resultados:** `resumen.md` de la corrida B (disponibilidad por fase, detección, p95) y, para contrastar, el de la línea base A (0 % en la fase de falla).

**Decir:** qué está pasando en cada momento, y cerrar con la conclusión: hipótesis confirmada o no, según los números reales.

## Antes de subir

- Duración ≤ 8:00 y reproducible sin descargar (YouTube no listado, Drive o similar).
- Pega la URL en Hélix: Proyecto → Arquitectura de Software → Experimentos → EXP-009 → Resultados y análisis → Enlaces y evidencias → + Agregar evidencia.
