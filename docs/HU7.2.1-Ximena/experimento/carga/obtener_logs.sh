#!/usr/bin/env bash
# EXP-006 (H7.2.1) - Descarga de CloudWatch Logs los eventos JSON de Siniestros
# (intento_fallido, pago_confirmado, pago_fallido_definitivo) y de Pagos
# (replica_iniciada, falla_inyectada) para la ventana de la corrida.
#
#   ./obtener_logs.sh <carpeta_salida> <inicio_ms> <fin_ms>
set -euo pipefail
source ~/exp006.env
OUT=$1; DESDE=$2; HASTA=$3

aws logs filter-log-events --log-group-name "$LOG_GROUP" \
  --log-stream-name-prefix siniestros --start-time "$DESDE" --end-time "$HASTA" \
  --filter-pattern '{ $.evento = "intento_fallido" || $.evento = "pago_confirmado" || $.evento = "pago_fallido_definitivo" }' \
  --query 'events[].message' --output json | jq -c '.[] | fromjson' > "$OUT/siniestros-eventos.jsonl"

aws logs filter-log-events --log-group-name "$LOG_GROUP" \
  --log-stream-name-prefix pagos --start-time "$DESDE" --end-time "$HASTA" \
  --filter-pattern '{ $.evento = "replica_iniciada" || $.evento = "falla_inyectada" }' \
  --query 'events[].message' --output json | jq -c '.[] | fromjson' > "$OUT/pagos-eventos.jsonl"

echo "siniestros: $(wc -l < "$OUT/siniestros-eventos.jsonl") eventos | pagos: $(wc -l < "$OUT/pagos-eventos.jsonl") eventos"
