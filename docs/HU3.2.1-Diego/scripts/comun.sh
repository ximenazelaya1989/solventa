#!/usr/bin/env bash
# Variables y funciones comunes de los scripts de EXP-007 (se incluye con `source`).
# shellcheck disable=SC2034  # RAIZ y REGISTRO los usan los scripts que incluyen este archivo
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
PILA="${PILA:-solventa-exp007}"
TAG="${TAG:-exp007}"
SECRETOS="${SECRETOS:-$HOME/exp007}"   # fuera del repo: certificado, llave privada y secreto del JWT
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP="$(cd "$AQUI/.." && pwd)"                 # docs/HU3.2.1-Diego
RAIZ="$(cd "$EXP/../.." && pwd)"              # raiz del repo
LLAVE="${LLAVE:-$HOME/Downloads/labsuser.pem}"

verde() { printf '\033[32m%s\033[0m\n' "$*"; }
azul() { printf '\033[36m%s\033[0m\n' "$*"; }
rojo() { printf '\033[31m%s\033[0m\n' "$*" >&2; }

verificar_credenciales() {
  if ! CUENTA=$(aws sts get-caller-identity --query Account --output text 2>/dev/null); then
    rojo "Credenciales de AWS invalidas o vencidas."
    rojo "Learner Lab > AWS Details > AWS CLI: Show > copiar el bloque en ~/.aws/credentials"
    exit 1
  fi
  REGISTRO="$CUENTA.dkr.ecr.$REGION.amazonaws.com"
}

ip_ec2() {
  aws ec2 describe-instances --region "$REGION" \
    --filters "Name=tag:aws:cloudformation:stack-name,Values=$PILA" \
              "Name=tag:aws:cloudformation:logical-id,Values=Carga" \
              "Name=instance-state-name,Values=running" \
    --query "Reservations[0].Instances[0].PublicIpAddress" --output text
}
