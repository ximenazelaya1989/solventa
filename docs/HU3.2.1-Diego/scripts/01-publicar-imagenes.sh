#!/usr/bin/env bash
# EXP-007 · Paso 1: construye las 3 imagenes del experimento y las sube a Amazon ECR.
# Requisitos: Docker Desktop abierto y credenciales del Learner Lab en ~/.aws/credentials.
#
#   ./01-publicar-imagenes.sh
source "$(dirname "$0")/comun.sh"
verificar_credenciales
azul "Cuenta $CUENTA · registro $REGISTRO · tag $TAG"

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRO"

for servicio in consentimiento perfilamiento mock-open-finance; do
  repo="solventa-$servicio"
  if ! aws ecr describe-repositories --region "$REGION" --repository-names "$repo" >/dev/null 2>&1; then
    azul "Creando repositorio $repo"
    aws ecr create-repository --region "$REGION" --repository-name "$repo" >/dev/null
  fi
  imagen="$REGISTRO/$repo:$TAG"
  azul "Construyendo $imagen"
  # --platform: el Mac es ARM y Fargate corre en x86_64
  docker build --platform linux/amd64 -t "$imagen" "$RAIZ/services/$servicio"
  docker push "$imagen"
done
verde "Imagenes publicadas en ECR."
