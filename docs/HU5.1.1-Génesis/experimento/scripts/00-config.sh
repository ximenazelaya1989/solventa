#!/usr/bin/env bash
# EXP-010 (HU5.1.1) - variables comunes de los scripts. Se carga con "source".
set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export PILA="${PILA:-solventa-exp010}"
EXP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export EXP_DIR
REPO_DIR="$(cd "$EXP_DIR/../../.." && pwd)"
export REPO_DIR
export RESULTADOS_DIR="$EXP_DIR/../resultados"
mkdir -p "$RESULTADOS_DIR"

salida() { # valor de un Output de la pila
  aws cloudformation describe-stacks --stack-name "$PILA" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}
