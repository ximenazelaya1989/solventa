#!/usr/bin/env bash
# EXP-010 - Pide a Cognito los tokens de prueba (OAuth2 client_credentials) y
# arma los de los casos negativos. Deja todo en resultados/tokens.properties
# (para JMeter). Ese archivo tiene tokens: no se sube al repositorio.
#
#   ./03-obtener-tokens.sh
source "$(dirname "$0")/00-config.sh"
POOL="$(salida UserPoolId)"
TOKEN_URL="$(salida TokenUrl)"
API_URL="$(salida ApiUrl)"

token() { # $1 = client id
  local secreto
  secreto="$(aws cognito-idp describe-user-pool-client --user-pool-id "$POOL" --client-id "$1" \
    --query 'UserPoolClient.ClientSecret' --output text)"
  curl -sf -u "$1:$secreto" -X POST "$TOKEN_URL" \
    -H 'content-type: application/x-www-form-urlencoded' \
    -d 'grant_type=client_credentials' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
}

echo "Pidiendo tokens a $TOKEN_URL"
TOKEN_A="$(token "$(salida ClienteSocioA)")"
TOKEN_B="$(token "$(salida ClienteSocioB)")"
TOKEN_SIN_SCOPE="$(token "$(salida ClienteSocioASinScope)")"
TOKEN_EXPIRA="$(token "$(salida ClienteSocioAExpira)")"   # vive 5 minutos

# Caso 2: token valido del socio A con la firma alterada (se cambia un caracter
# en medio de la firma; la cabecera y el contenido quedan intactos).
TOKEN_ALTERADO="$(python3 - "$TOKEN_A" <<'PY'
import sys
cab, cont, firma = sys.argv[1].split(".")
i = len(firma) // 2
firma = firma[:i] + ("A" if firma[i] != "A" else "B") + firma[i + 1:]
print(f"{cab}.{cont}.{firma}")
PY
)"

ARCHIVO="$RESULTADOS_DIR/tokens.properties"
{
  echo "host=${API_URL#https://}"
  echo "client_id_a=$(salida ClienteSocioA)"
  echo "token_a=$TOKEN_A"
  echo "token_b=$TOKEN_B"
  echo "token_sin_scope=$TOKEN_SIN_SCOPE"
  echo "token_expirado=$TOKEN_EXPIRA"
  echo "token_alterado=$TOKEN_ALTERADO"
  echo "token_expirado_emitido=$(date +%s)"
} > "$ARCHIVO"
chmod 600 "$ARCHIVO"
echo "Tokens en $ARCHIVO"
echo "El token del caso 3 expira en 5 minutos: corre 04-ejecutar-casos.sh despues de esa hora"
echo "(el script espera solo si hace falta)."
