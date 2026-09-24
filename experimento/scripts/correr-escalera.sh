#!/usr/bin/env bash
# =============================================================================
# Experimento HU2.1.1 · Escalera de niveles de carga
# Se ejecuta en la EC2 generadora de carga (solventa-loadgen), desde experimento/.
#
#   export BASE_URL=http://<IP_PRIVADA_APP>:3000
#   export DB_HOST=<IP_PRIVADA_DB>
#   ./scripts/correr-escalera.sh                    # todos los niveles
#   ./scripts/correr-escalera.sh operacion-normal   # solo un nivel
#
# Antes de CADA corrida: BD a estado semilla -> verificación /health ->
# enfriamiento -> k6. Los resultados quedan en resultados/<nivel>-rep<N>.json
# =============================================================================
set -euo pipefail

: "${BASE_URL:?Defina BASE_URL, p. ej. http://10.0.1.23:3000}"
: "${DB_HOST:?Defina DB_HOST (IP privada de solventa-db)}"
export PGPASSWORD="${DB_PASSWORD:-solventa}"
ENFRIAMIENTO="${ENFRIAMIENTO:-60}"
FILTRO="${1:-}"

# nombre:TPS:duración_en_segundos:repeticiones
NIVELES=(
  "smoke:2:60:1"
  "carga-baja:10:180:4"
  "carga-media:25:180:4"
  "operacion-normal:50:180:8"
  "carga-alta:100:180:4"
  "carga-muy-alta:200:180:4"
  "estres:400:180:8"
)

cd "$(dirname "$0")/.."
mkdir -p resultados

for spec in "${NIVELES[@]}"; do
  IFS=: read -r nivel tps segundos reps <<< "$spec"
  if [[ -n "$FILTRO" && "$FILTRO" != "$nivel" ]]; then continue; fi
  # Cotizaciones necesarias: TPS x segundos + 20 % de holgura
  n=$(( tps * segundos * 12 / 10 + 100 ))
  for rep in $(seq 1 "$reps"); do
    echo ">>> $(date +%T) · $nivel · rep $rep/$reps · $tps TPS · semilla n=$n"
    (cd seed && psql -h "$DB_HOST" -U solventa -d solventa -v n="$n" -q -f reset-y-semilla.sql)
    curl -fsS "$BASE_URL/health" > /dev/null || { echo "La API no responde en $BASE_URL/health"; exit 1; }
    echo "    enfriamiento ${ENFRIAMIENTO}s ..."
    sleep "$ENFRIAMIENTO"
    k6 run -q \
      -e BASE_URL="$BASE_URL" -e TPS="$tps" -e DURACION="${segundos}s" \
      -e NIVEL="$nivel" -e REP="$rep" -e CSV=../seed/cotizaciones.csv \
      k6/suscripcion.js || echo "    (k6 terminó con umbrales incumplidos: el resultado se registra igual)"
  done
done
echo ">>> Escalera terminada. Resultados en $(pwd)/resultados"
