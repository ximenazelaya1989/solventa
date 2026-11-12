# EXP-010 · Resumen de la corrida 2026-11-12 03:09 UTC

**Hipótesis: CONFIRMADA** (100 % de códigos esperados y ninguna petición rechazada registrada en un componente que no debía alcanzar).

Cuenta AWS propia, región us-east-2. Ejecutado desde AWS CloudShell con `04-ejecutar-casos.sh` (runner en Python, sin carga).

| Caso | Descripción | Esperado | Aciertos | % | Quién rechaza |
|---|---|---|---|---|---|
| C1 | Sin token | 401 | 20/20 | 100 | AWS API Gateway (borde) |
| C2 | Token con la firma alterada | 401 | 20/20 | 100 | AWS API Gateway (borde) |
| C3 | Token expirado | 401 | 20/20 | 100 | AWS API Gateway (borde) |
| C4 | Token sin scope cotizaciones/crear | 403 | 20/20 | 100 | AWS API Gateway (borde) |
| C5 | Socio A pide para un cliente del socio B | 403 | 20/20 | 100 | Distribución y socios |
| C6 | Socio A pide para su propio cliente | 201 | 20/20 | 100 | — (llega a Cotización) |
| C7 | Bypass: directo al gateway interno | 403 | 5/5 | 100 | api-gateway interno |

## Verificación con CloudWatch Logs Insights

| Verificación | Esperado | Obtenido | Cumple |
|---|---|---|---|
| AWS API Gateway: 401 sin invocar la integración (C1–C3) | 60 | 60 | sí |
| AWS API Gateway: 403 por scope sin invocar la integración (C4) | 20 | 20 | sí |
| AWS API Gateway: reenviadas que terminaron en 403 (C5) | 20 | 20 | sí |
| AWS API Gateway: reenviadas que terminaron en 201 (C6) | 20 | 20 | sí |
| Gateway interno: peticiones recibidas desde el borde (solo C5 y C6) | 40 | 40 | sí |
| Gateway interno: bypass rechazado por falta del secreto de origen | 5 | 5 | sí |
| Distribución y socios: peticiones recibidas (solo C5 y C6) | 40 | 40 | sí |
| Distribución y socios: 403 por cliente de otro socio (C5) | 20 | 20 | sí |
| Distribución y socios: llamadas a Cotización (solo C6) | 20 | 20 | sí |
| Cotización: POST /cotizaciones recibidos (solo C6) | 20 | 20 | sí |

Los archivos crudos (`resultados.csv`, `logs-*.json`, `resumen.json`) quedaron en CloudShell en `~/solventa/docs/HU5.1.1-Génesis/resultados/corrida-20261112-030928/`.
