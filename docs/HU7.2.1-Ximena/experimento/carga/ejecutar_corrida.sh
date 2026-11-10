#!/usr/bin/env bash
# EXP-006 (H7.2.1) - Ejecuta UNA corrida completa del experimento:
#   1. vacia las tablas (pagos y siniestros)
#   2. arranca la sonda de Aurora (cada 200 ms)
#   3. lanza k6: 10.000 ordenes a 10 TPS (~17 min)
#   4. inyecta las fallas en los minutos 5 y 10
#   5. verifica perdidas y duplicados, descarga los logs y analiza
#
#   ./ejecutar_corrida.sh tacticas-1
#   ./ejecutar_corrida.sh control-1
#   TPS=1 DURACION=60s T_PAGOS=20 T_AURORA=40 ./ejecutar_corrida.sh piloto   # corrida corta
set -euo pipefail
cd "$(dirname "$0")"
source ~/exp006.env

NOMBRE=${1:?uso: ejecutar_corrida.sh <nombre>}
OUT=~/resultados/$NOMBRE
mkdir -p "$OUT"
export PGPASSWORD=$DB_PASSWORD PGSSLMODE=require

# Modo de la corrida segun la tarea de Siniestros desplegada
TD=$(aws ecs describe-services --cluster "$ECS_CLUSTER" --services siniestros \
  --query 'services[0].taskDefinition' --output text)
MODO=$(aws ecs describe-task-definition --task-definition "$TD" \
  --query "taskDefinition.containerDefinitions[0].environment[?name=='RETRY_IDEMPOTENCY_ENABLED'].value" --output text)
echo "Corrida $NOMBRE | RETRY_IDEMPOTENCY_ENABLED=$MODO"

echo "Vaciando tablas..."
psql -h "$AURORA_WRITER" -U "$DB_USER" -d pagos_db -qc "TRUNCATE pagos; DROP TABLE IF EXISTS sonda_failover;"
psql -h "$SINIESTROS_DB" -U "$DB_USER" -d siniestros_db -qc "TRUNCATE siniestros;"
sleep 30   # estabilizacion

INICIO=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ); INICIO_MS=$(date +%s%3N)
python3 sonda.py --salida "$OUT/sonda.csv" & SONDA=$!
./inyectar_fallas.sh "$OUT/inyecciones.csv" > "$OUT/inyecciones.log" 2>&1 & INY=$!

k6 run --out csv="$OUT/k6.csv" --summary-export="$OUT/k6-resumen.json" \
  -e SINIESTROS_URL="$SINIESTROS_URL" -e TPS="${TPS:-10}" -e DURACION="${DURACION:-1000s}" \
  carga.js 2>&1 | tee "$OUT/k6-consola.txt" || true

wait $INY || true
sleep 20
kill $SONDA 2>/dev/null || true; wait $SONDA 2>/dev/null || true
FIN=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ); FIN_MS=$(date +%s%3N)

cat > "$OUT/corrida.json" <<EOF
{"nombre": "$NOMBRE", "retry_idempotency_enabled": "$MODO", "inicio": "$INICIO", "fin": "$FIN",
 "tps": "${TPS:-10}", "duracion": "${DURACION:-1000s}", "task_definition_siniestros": "$TD"}
EOF

echo "Verificando perdidas y duplicados..."
python3 verificar.py --salida "$OUT/verificacion.json"
echo "Descargando logs de CloudWatch..."
./obtener_logs.sh "$OUT" "$INICIO_MS" "$FIN_MS"
echo "Analizando..."
python3 analizar.py "$OUT"
echo "Listo: $OUT"
