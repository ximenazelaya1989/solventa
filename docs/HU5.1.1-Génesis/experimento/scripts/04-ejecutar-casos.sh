#!/usr/bin/env bash
# EXP-010 - Ejecuta una corrida: los 6 casos x 20 peticiones contra el AWS API
# Gateway de borde (JMeter si esta instalado; si no, el script de Python
# equivalente), la prueba de bypass, la recoleccion de logs y el analisis.
#
#   ./04-ejecutar-casos.sh            # usa JMeter si existe (brew install jmeter)
#   USAR_PYTHON=1 ./04-ejecutar-casos.sh
source "$(dirname "$0")/00-config.sh"
PROPS="$RESULTADOS_DIR/tokens.properties"
[ -f "$PROPS" ] || { echo "Primero corre 03-obtener-tokens.sh"; exit 1; }
CORRIDA="$RESULTADOS_DIR/corrida-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$CORRIDA"
BYPASS="$(salida GatewayInternoUrl)"

# El token del caso 3 debe haber expirado (vive 5 min) antes de empezar.
EMITIDO="$(grep '^token_expirado_emitido=' "$PROPS" | cut -d= -f2)"
ESPERA=$(( EMITIDO + 330 - $(date +%s) ))
if [ "$ESPERA" -gt 0 ]; then echo "Esperando ${ESPERA}s a que expire el token del caso 3..."; sleep "$ESPERA"; fi

if command -v jmeter >/dev/null && [ -z "${USAR_PYTHON:-}" ]; then
  INICIO=$(date +%s)
  jmeter -n -t "$EXP_DIR/pruebas/exp010.jmx" -q "$PROPS" -l "$CORRIDA/resultados.jtl" \
    -e -o "$CORRIDA/reporte-jmeter" -j "$CORRIDA/jmeter.log"
  # Bypass: peticion directa al gateway interno, sin pasar por el borde (5 veces).
  python3 "$EXP_DIR/pruebas/ejecutar_casos.py" --props "$PROPS" --salida "$CORRIDA/bypass" \
    --peticiones 0 --bypass "$BYPASS"
  FIN=$(date +%s)
  printf '{"inicio": %s, "fin": %s, "peticiones": 20}\n' "$INICIO" "$FIN" > "$CORRIDA/ventana.json"
else
  echo "(JMeter no encontrado o USAR_PYTHON=1: se usa ejecutar_casos.py)"
  python3 "$EXP_DIR/pruebas/ejecutar_casos.py" --props "$PROPS" --salida "$CORRIDA" --bypass "$BYPASS"
fi

echo "Esperando 60 s a que CloudWatch reciba los logs..."
sleep 60
"$(dirname "$0")/05-recolectar-logs.sh" "$CORRIDA"
python3 "$EXP_DIR/pruebas/analizar.py" "$CORRIDA"
echo "Corrida completa en $CORRIDA (ver resumen.md)"
