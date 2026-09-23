#!/usr/bin/env bash
# Publica una version SANA de reglas y la aplica instancia por instancia,
# verificando health antes de pasar a la siguiente.
# Uso: ./rolling-update-sano.sh <ip_instancia1:puerto> <ip_instancia2:puerto>
set -euo pipefail

INSTANCIA_1=${1:?"Falta ip:puerto de la instancia 1, ej. 10.0.1.10:3000"}
INSTANCIA_2=${2:?"Falta ip:puerto de la instancia 2, ej. 10.0.1.11:3000"}

echo "== Publicando nueva version de reglas =="
RESPUESTA=$(curl -s -X POST "http://${INSTANCIA_1}/rating/reglas" \
  -H "Content-Type: application/json" \
  -d '{"factores": {"bajo": 1.0, "medio": 1.35, "alto": 1.9}}')
echo "$RESPUESTA"
VERSION=$(echo "$RESPUESTA" | grep -o '"version":[0-9]*' | grep -o '[0-9]*')
echo "Nueva version publicada: v$VERSION"

for INSTANCIA in "$INSTANCIA_1" "$INSTANCIA_2"; do
  echo ""
  echo "== [$(date -u +%H:%M:%S)] Aplicando v$VERSION en $INSTANCIA =="
  curl -s -X POST "http://${INSTANCIA}/rating/reglas/aplicar" \
    -H "Content-Type: application/json" -d "{\"version\": $VERSION}"
  echo ""
  echo "-- Health de $INSTANCIA --"
  curl -s "http://${INSTANCIA}/rating/health"
  echo ""
  echo "Instancia $INSTANCIA lista. Esperando 5s antes de continuar..."
  sleep 5
done

echo ""
echo "== Rolling update completo. Ambas instancias en v$VERSION =="
echo "Revisa el k6 corriendo en paralelo: el error rate deberia seguir en 0% durante todo este proceso."