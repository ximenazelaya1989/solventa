#!/usr/bin/env bash
# EXP-010 - Cuenta, con CloudWatch Logs Insights, que paso en cada componente
# durante la ventana de la corrida. Es la evidencia de que las peticiones
# rechazadas en el borde NO llegaron al gateway interno ni a los microservicios.
#
#   ./05-recolectar-logs.sh <carpeta-de-corrida>
source "$(dirname "$0")/00-config.sh"
CORRIDA="${1:?Uso: ./05-recolectar-logs.sh <carpeta-de-corrida>}"
INICIO="$(python3 -c "import json;print(json.load(open('$CORRIDA/ventana.json'))['inicio']-5)")"
FIN="$(python3 -c "import json;print(json.load(open('$CORRIDA/ventana.json'))['fin']+5)")"
LG_ECS="$(salida LogGroupServicios)"
LG_BORDE="$(salida LogGroupBorde)"

consulta() { # $1 archivo, $2 log group, $3 query
  local id estado
  id="$(aws logs start-query --log-group-name "$2" --start-time "$INICIO" --end-time "$FIN" \
    --query-string "$3" --query 'queryId' --output text)"
  for _ in $(seq 1 30); do
    sleep 2
    estado="$(aws logs get-query-results --query-id "$id" --query 'status' --output text)"
    [ "$estado" = "Complete" ] && break
  done
  aws logs get-query-results --query-id "$id" > "$CORRIDA/$1"
  echo "  $1 ($estado)"
}

echo "Consultando CloudWatch Logs ($INICIO - $FIN)"
consulta logs-borde.json "$LG_BORDE" \
  'stats count(*) as n by status, integrationStatus, errorAutorizador'
consulta logs-servicios.json "$LG_ECS" \
  'filter exp = "EXP-010" and evento != "semilla_cargada" | stats count(*) as n by servicio, evento, motivo'
consulta logs-cotizacion.json "$LG_ECS" \
  'filter @logStream like /^cotizacion/ and @message like /POST \/cotizaciones/ | stats count(*) as n'
