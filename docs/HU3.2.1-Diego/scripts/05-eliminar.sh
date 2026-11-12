#!/usr/bin/env bash
# EXP-007 · Paso 5: borra toda la infraestructura para no gastar creditos del laboratorio.
# Las imagenes de ECR y el certificado se conservan (no cuestan casi nada) salvo que se pida.
#
#   ./05-eliminar.sh            borra la pila (RDS, ECS, ALB, EC2)
#   ./05-eliminar.sh --todo     ademas borra los repositorios de ECR y el certificado
source "$(dirname "$0")/comun.sh"
verificar_credenciales

azul "Eliminando la pila $PILA (tarda ~10 min)..."
aws cloudformation delete-stack --region "$REGION" --stack-name "$PILA"
aws cloudformation wait stack-delete-complete --region "$REGION" --stack-name "$PILA"
verde "Pila eliminada."

if [ "${1:-}" = "--todo" ]; then
  for servicio in consentimiento perfilamiento mock-open-finance; do
    aws ecr delete-repository --region "$REGION" --repository-name "solventa-$servicio" --force >/dev/null 2>&1 \
      && echo "Repositorio solventa-$servicio eliminado"
  done
  if [ -s "$SECRETOS/cert_arn.txt" ]; then
    arn=$(cat "$SECRETOS/cert_arn.txt")
    case "$arn" in
      arn:aws:acm:*) aws acm delete-certificate --region "$REGION" --certificate-arn "$arn" ;;
      arn:aws:iam:*) aws iam delete-server-certificate --server-certificate-name solventa-exp007 ;;
    esac
    rm -f "$SECRETOS/cert_arn.txt"
    echo "Certificado eliminado"
  fi
fi
