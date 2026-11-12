#!/usr/bin/env bash
# EXP-010 - Borra la pila completa para no gastar creditos del Learner Lab.
#   ./06-eliminar.sh            (las imagenes de ECR se conservan)
#   BORRAR_ECR=1 ./06-eliminar.sh
source "$(dirname "$0")/00-config.sh"
aws cloudformation delete-stack --stack-name "$PILA"
echo "Eliminando $PILA (tarda varios minutos)..."
aws cloudformation wait stack-delete-complete --stack-name "$PILA"
if [ -n "${BORRAR_ECR:-}" ]; then
  for s in api-gateway distribucion-socios cotizacion perfilamiento; do
    aws ecr delete-repository --repository-name "solventa-$s" --force >/dev/null && echo "ECR solventa-$s borrado"
  done
fi
echo "Listo."
