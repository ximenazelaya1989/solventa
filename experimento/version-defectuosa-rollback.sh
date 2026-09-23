#!/usr/bin/env bash
# Publica una version DEFECTUOSA y la aplica en UNA sola instancia,
# para medir tiempo de deteccion de falla y tiempo de rollback automatico.
# Uso: ./version-defectuosa-rollback.sh <ip_instancia:puerto>
set -euo pipefail

INSTANCIA=${1:?"Falta ip:puerto de la instancia, ej. 10.0.1.10:3000"}

echo "== Publicando version defectuosa (fallaSanityCheck=true) =="
RESPUESTA=$(curl -s -X POST "http://${INSTANCIA}/rating/reglas" \
  -H "Content-Type: application/json" \
  -d '{"factores": {"bajo": 1.0}, "fallaSanityCheck": true}')
echo "$RESPUESTA"
VERSION=$(echo "$RESPUESTA" | grep -o '"version":[0-9]*' | grep -o '[0-9]*')

T0=$(date +%s)
echo ""
echo "== [$(date -u +%H:%M:%S)] Aplicando v$VERSION (defectuosa) en $INSTANCIA =="
curl -s -X POST "http://${INSTANCIA}/rating/reglas/aplicar" \
  -H "Content-Type: application/json" -d "{\"version\": $VERSION}"
echo ""

echo ""
echo "== Monitoreando /rating/health cada 2s (hasta 90s) =="
for i in $(seq 1 45); do
  ESTADO=$(curl -s -o /dev/null -w "%{http_code}" "http://${INSTANCIA}/rating/health")
  AHORA=$(date +%s)
  TRANSCURRIDO=$((AHORA - T0))
  echo "t+${TRANSCURRIDO}s  [$(date -u +%H:%M:%S)]  HTTP: $ESTADO"
  if [ "$ESTADO" = "200" ] && [ "$TRANSCURRIDO" -gt 2 ]; then
    echo ""
    echo "Recuperada (rollback automatico) en t+${TRANSCURRIDO}s desde que se aplico la version defectuosa."
    exit 0
  fi
  sleep 2
done

echo "No se recupero dentro de la ventana de monitoreo (revisa logs de la instancia)."