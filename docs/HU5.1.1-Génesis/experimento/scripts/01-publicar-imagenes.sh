#!/usr/bin/env bash
# EXP-010 - Construye y publica en Amazon ECR las imagenes de los 4 servicios
# del experimento: api-gateway, distribucion-socios, cotizacion y perfilamiento.
# Requisitos: Docker Desktop abierto y credenciales del Learner Lab en ~/.aws/credentials.
#
#   ./01-publicar-imagenes.sh
source "$(dirname "$0")/00-config.sh"
TAG="${1:-latest}"

CUENTA="$(aws sts get-caller-identity --query Account --output text)"
REGISTRO="$CUENTA.dkr.ecr.$AWS_REGION.amazonaws.com"
echo "Cuenta $CUENTA - registro $REGISTRO"
aws ecr get-login-password | docker login --username AWS --password-stdin "$REGISTRO"

for servicio in api-gateway distribucion-socios cotizacion perfilamiento; do
  repo="solventa-$servicio"
  aws ecr describe-repositories --repository-names "$repo" >/dev/null 2>&1 \
    || aws ecr create-repository --repository-name "$repo" >/dev/null
  imagen="$REGISTRO/$repo:$TAG"
  echo "==> $imagen"
  # --platform: Fargate corre en x86_64 aunque el Mac sea ARM (M1/M2/M3)
  docker build --platform linux/amd64 -t "$imagen" "$REPO_DIR/services/$servicio"
  docker push "$imagen"
done
echo "Imagenes publicadas."
