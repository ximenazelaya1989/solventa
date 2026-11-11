# EXP-009 · Checklist de capturas y evidencia

Marca cada una cuando la tengas. Guárdalas en `docs/HU10.1.3-Giovanna/evidencias/` con nombres claros (por ejemplo `01-ecr-repositorios.png`). Procura que se vea la **región (us-east-1)** y la hora.

## Montaje (una vez)

- [ ] ECR: los 4 repositorios con la imagen subida
- [ ] Security groups creados
- [ ] RDS PostgreSQL: estado *Disponible* (y sus dos bases creadas)
- [ ] ElastiCache Redis: estado *Disponible*, 1 nodo
- [ ] ECS: cluster con los 4 servicios, tareas en *Running* y su número deseado (2/2/2/1)
- [ ] Task definition de Perfilamiento con las variables (flags visibles, sin secretos)
- [ ] ALB: listener con las reglas por ruta
- [ ] Target groups: todos *healthy* (en especial Perfilamiento con `/ready`)
- [ ] EC2 de carga en ejecución
- [ ] Una cotización real por el ALB devolviendo precio (terminal)

## Por cada corrida (B-503, B-2s, A-503)

- [ ] El flag `CIRCUIT_BREAKER_ENABLED` configurado (true/false) en el task definition
- [ ] `preparar_datos.py` terminado (clientes creados, caché calentada)
- [ ] Locust en ejecución (terminal o UI)
- [ ] El momento de la falla inyectada (línea `FALLA inyectada`)
- [ ] `/admin/open-finance/estado` durante la falla (circuito ABIERTO, contadores)
- [ ] CloudWatch Logs con `evento=CIRCUITO` y `evento=DEGRADADO`
- [ ] El momento de la restauración (línea `Open Finance RESTAURADO`)
- [ ] Resumen final de `analizar.py`
- [ ] Carpeta de resultados copiada a tu computador (`requests.csv`, `estado_final.json`, `resumen.json`, `resumen.md`)

## Al terminar

- [ ] Resultados guardados también en `docs/HU10.1.3-Giovanna/resultados/`
- [ ] Video grabado y subido; URL pegada en Hélix
- [ ] PDF en `docs/HU10.1.3-Giovanna/`; URL pegada en Hélix
- [ ] Todo apagado en AWS (ECS, ALB, RDS, ElastiCache, EC2, ECR) y verificado en la consola
