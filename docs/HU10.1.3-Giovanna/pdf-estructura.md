# EXP-009 · Estructura del PDF de resultados y análisis

La entrega pide: **resultados, análisis de resultados y conclusión**. Este esquema indica qué va en cada sección y de dónde sale cada dato. Los campos `[ ]` se llenan con los números de las corridas en AWS (`resumen.json` / `resumen.md` de cada corrida).

El PDF final va en `docs/HU10.1.3-Giovanna/` y su URL se pega en Hélix (Resultados y análisis → Enlaces y evidencias → Informe externo).

---

## 1. Resumen (media página)
Una frase del objetivo, una del método y el veredicto (hipótesis confirmada / refutada / inconclusa) con los 3 números clave: disponibilidad en la fase de falla, tiempo de detección y p95.

## 2. Contexto y escenario de calidad
- HU10.1.3 y su escenario: Disponibilidad, Orquestador de integraciones externas, Open Finance caído, ≥ 99,9 %, detección ≤ 5 s.
- Hipótesis de diseño (texto del experimento) y condiciones de refutación.

## 3. Diseño del experimento
- **Arquitectura bajo prueba:** diagrama de componentes y de despliegue (con las tácticas marcadas).
- **Tácticas:** timeout 120 ms, circuit breaker (50 % en 10 llamadas, 30 s abierto, 3 pruebas), bulkhead de 10, caché en Redis (24 h máx.), perfil por defecto, readiness solo Redis.
- **Configuraciones:**

| | Open Finance | Circuit breaker, bulkhead, caché y degradación |
|---|---|---|
| A (línea base) | consultado, timeout 120 ms | apagados |
| B | consultado, timeout 120 ms | activos |

- **Carga:** 10 TPS constantes, 20 min, fases 5/10/5 min; 1.000 clientes (800 con caché, 20 % sin ella); fallas: 503 y latencia de 2 s.
- **Infraestructura:** tabla de recursos de AWS (ECS Fargate, ALB, RDS, ElastiCache, EC2), tareas por servicio, región.
- **Métricas y criterios de aceptación:**

| Métrica | Criterio |
|---|---|
| Disponibilidad en la fase de falla | ≥ 99,9 % |
| Tiempo de detección (falla → circuito abierto) | ≤ 5 s |
| p95 / p99 de cotización | ≤ 250 ms / ≤ 500 ms |
| % servido desde caché / con perfil por defecto | informativo (esperado ≈ 80 / 20) |
| Tiempo de recuperación | informativo (esperado ≈ 0–35 s) |

## 4. Resultados
Una subsección por corrida (B-503, B-2s, A-503), cada una con:

| Fase | Solicitudes | Fallos | Disponibilidad | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|
| 1 normal | [ ] | [ ] | [ ] | [ ] | [ ] |
| 2 falla | [ ] | [ ] | [ ] | [ ] | [ ] |
| 3 recuperación | [ ] | [ ] | [ ] | [ ] | [ ] |

Y debajo: tiempo de detección por tarea, tiempo de recuperación, % caché / por defecto, transiciones del circuito (con hora) y contadores de Perfilamiento.

**Gráficas sugeridas** (se arman con `requests.csv`): (a) disponibilidad por fase, A vs. B; (b) latencia p95 por fase; (c) línea de tiempo del circuito (CERRADO → ABIERTO → SEMIABIERTO → CERRADO) sobre las cotizaciones por segundo.

**Tabla comparativa final:**

| | A-503 | B-503 | B-2s |
|---|---|---|---|
| Disponibilidad total | [ ] | [ ] | [ ] |
| Disponibilidad en la falla | [ ] | [ ] | [ ] |
| Detección | n/a | [ ] | [ ] |
| p95 en la falla | [ ] | [ ] | [ ] |

## 5. Análisis de resultados
- **Criterio por criterio:** cumple / no cumple, con el número.
- **A frente a B:** qué cambia con las tácticas y por qué (el circuito corta las esperas; la caché y el perfil por defecto mantienen el precio).
- **Latencia:** por qué baja en la fase de falla (se deja de esperar a Open Finance) y qué pasa en la recuperación (llamadas de prueba).
- **Recuperación:** depende del momento del ciclo en que se restaura (abierto 30 s).
- **Calidad de la respuesta degradada:** cuántas cotizaciones usaron el perfil por defecto y qué implica para el negocio (precio más conservador).
- **Qué no se probó / limitaciones:**
  - Redis de un solo nodo: no se probó su caída ni la de una zona.
  - Carga de 10 TPS; no se probó el escalado a 500→50.000/min.
  - Mock de Open Finance, no el proveedor real; latencia de red de AWS.
  - Dos tareas de Perfilamiento con circuito independiente cada una.
  - **Caché de 24 h frente a la revocación de consentimiento en ≤ 5 min (HU3.2.1):** un perfil en caché de un cliente que revocó podría usarse mientras Open Finance esté caído. Mitigación: invalidar la entrada al revocar; no probada aquí.
  - Medición: calentamiento previo de 30 peticiones sin medir; tiempos tomados del reloj del mock.

## 6. Conclusión
Veredicto de la hipótesis (confirmada / refutada / inconclusa), qué decisión de arquitectura sustenta (degradación + aislamiento frente a dependencias externas) y recomendaciones (invalidación de caché por revocación, Redis con réplica, alertas sobre el estado del circuito).

## 7. Anexos
- Capturas de la consola de AWS y de CloudWatch.
- Enlaces: repositorio (rama y carpeta), video.
- Archivos de cada corrida (`requests.csv`, `estado_final.json`, `resumen.json`, `resumen.md`).
- Código de las tácticas: `services/perfilamiento/app/open_finance.py` y `services/mock-open-finance/`.
- Uso de IA: herramienta, para qué se usó y cómo se verificó (si la entrega lo pide).
