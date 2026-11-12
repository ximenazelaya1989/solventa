# EXP-007 · Revocación efectiva de consentimiento Open Finance (HU3.2.1)

Hipótesis: con validación de consentimiento en Perfilamiento contra Consentimiento Open Finance
y una caché local de TTL 60 s, al revocar un consentimiento Perfilamiento responde 403 en
≤ 5 min (esperado ≈ 60 s) en el 100 % de los casos, sin accesos indebidos, sin rechazos falsos,
con p95 ≤ 300 ms y con el 100 % de las revocaciones en el `audit_log`.

## Dónde está cada táctica

| Táctica | Archivo |
|---|---|
| Autorizar actores, fail-closed | `services/perfilamiento/app/consentimiento.py` → `verificar_acceso` |
| Revocar acceso (caché TTL 60 s) | `services/perfilamiento/app/consentimiento.py` → `CacheConsentimiento`, `CONSENT_CACHE_TTL_S` |
| Autenticar actores (JWT + RBAC) | `services/consentimiento/app/seguridad.py` y `_autenticar` en Perfilamiento |
| Pista de auditoría | `services/consentimiento/app/main.py` → tabla `audit_log` (misma transacción que la revocación) |
| Database per Service | `consentimiento_db` solo la toca Consentimiento |
| Cifrado en tránsito / reposo | Listener HTTPS del ALB (certificado autofirmado en ACM) y RDS cifrada |

## Archivos

- `medicion/medir_revocacion.py`: precarga, token para JMeter, medición y análisis del `.jtl`.
- `jmeter/carga_fondo.jmx`: 10 TPS sobre `GET /perfiles/{clienteId}` con clientes que nunca se revocan.
- `infra/exp007.yaml`: CloudFormation con toda la infraestructura de AWS (RDS cifradas, ALB HTTPS, ECS, EC2 de carga).
- `scripts/`: `01` imágenes a ECR · `02` certificado y secreto JWT · `03` desplegar · `04` EC2 (subir/ssh/traer) · `05` eliminar.
- `medicion/resultados/`: `revocaciones.csv`, `resumen.json`, `jmeter.jtl`, `resumen_jmeter.json`, reporte HTML.

## Despliegue en AWS (resumen)

- ECS Fargate: Consentimiento, Perfilamiento y el mock de Open Finance.
- Un ALB con listener **HTTPS 443** (certificado autofirmado importado en ACM) y reglas por ruta:
  `/perfiles*` → Perfilamiento; `/consentimientos*` y `/auditoria*` → Consentimiento. Health check: `/health`.
- RDS PostgreSQL **cifrada** con `consentimiento_db` y `perfilamiento_db`.
- Variables de Perfilamiento: `CONSENT_CHECK_ENABLED=true`, `CONSENTIMIENTO_URL=https://<dns-del-alb>`,
  `CONSENT_CACHE_TTL_S=60`, `CONSENTIMIENTO_TLS_VERIFY=false` (o la ruta del certificado), `JWT_SECRET`.
  Para que la fuente de datos sea el mock: `OPEN_FINANCE_ENABLED=true`, `OPEN_FINANCE_URL=http://<dns-del-alb>:8080`.
  Los demás flags (`RATE_LIMIT_ENABLED`, `JWT_VALIDATION_ENABLED`, `CIRCUIT_BREAKER_ENABLED`, `RETRY_IDEMPOTENCY_ENABLED`) apagados.
- Variables de Consentimiento: `DATABASE_URL`, `JWT_SECRET` (la misma).
- EC2 para JMeter y el script: `pip install -r medicion/requirements.txt`.


## Ejecución

```bash
cd docs/HU3.2.1-Diego/medicion
export JWT_SECRET=<la de los servicios> PERF=https://<dns-del-alb> CONS=https://<dns-del-alb>

# 1. Precargar 50 clientes de medición + 50 de fondo
python medir_revocacion.py precargar --insecure

# 2. Carga de fondo (otra terminal), dura 25 min
jmeter -n -t ../jmeter/carga_fondo.jmx -Jprotocolo=https -Jhost=<dns-del-alb> -Jpuerto=443 \
  -Jtoken=$(python medir_revocacion.py token) \
  -l resultados/jmeter.jtl -e -o resultados/jmeter-reporte

# 3. Medición (≈ 12 min: 50 clientes escalonados cada 5 s, sondeo cada 2 s, 6 min de vigilancia)
python medir_revocacion.py medir --insecure --mock http://<mock>:8000

# 4. Cuando termine JMeter
python medir_revocacion.py jmeter resultados/jmeter.jtl
```

`--mock` es opcional: si el mock expone `llamadasPorCliente` en `/admin/estado`, el script verifica
que no hubo llamadas a Open Finance para un cliente después de su primer 403.

## Nota para el análisis

El paso (a) consulta el perfil justo antes de revocar, lo que llena la caché. Por eso Δt queda
cerca de 60 s + el intervalo de sondeo: se mide el **peor caso** de la caché, no un promedio
favorable. Si Perfilamiento corre con varias tareas, una tarea sin la entrada en caché responde 403
antes, así que Δt puede salir menor para algunos clientes.
