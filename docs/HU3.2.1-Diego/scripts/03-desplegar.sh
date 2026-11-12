#!/usr/bin/env bash
# EXP-007 · Paso 3: crea (o actualiza) la pila de CloudFormation con toda la infraestructura.
# Busca sola la VPC por defecto y una subred en us-east-1a y otra en us-east-1b.
# Tarda ~15 min (la mayor parte son las dos RDS).
#
#   ./03-desplegar.sh ClaveSoloLetrasYNumeros123
source "$(dirname "$0")/comun.sh"
DB_PASSWORD="${1:-}"
if ! printf '%s' "$DB_PASSWORD" | grep -Eq '^[A-Za-z0-9]{8,40}$'; then
  rojo "Uso: $0 <clave-de-las-RDS>   (solo letras y numeros, 8 a 40 caracteres)"
  exit 1
fi
verificar_credenciales
[ -s "$SECRETOS/cert_arn.txt" ] || { rojo "Falta el certificado: corre antes ./02-certificado-y-secretos.sh"; exit 1; }

VPC=$(aws ec2 describe-vpcs --region "$REGION" --filters Name=isDefault,Values=true \
      --query "Vpcs[0].VpcId" --output text)
subred() {
  aws ec2 describe-subnets --region "$REGION" \
    --filters "Name=vpc-id,Values=$VPC" "Name=availability-zone,Values=$1" "Name=default-for-az,Values=true" \
    --query "Subnets[0].SubnetId" --output text
}
SUB_A=$(subred us-east-1a)
SUB_B=$(subred us-east-1b)
if [ "$SUB_A" = "None" ] || [ "$SUB_B" = "None" ]; then
  rojo "No encontre subredes por defecto en us-east-1a / us-east-1b"; exit 1
fi
azul "VPC $VPC · us-east-1a=$SUB_A · us-east-1b=$SUB_B · pila $PILA"

if ! aws cloudformation deploy --region "$REGION" --stack-name "$PILA" \
     --template-file "$EXP/infra/exp007.yaml" \
     --parameter-overrides VpcId="$VPC" SubnetA="$SUB_A" SubnetB="$SUB_B" \
       CertificateArn="$(cat "$SECRETOS/cert_arn.txt")" DbPassword="$DB_PASSWORD" \
       JwtSecret="$(cat "$SECRETOS/jwt_secret.txt")" ImageTag="$TAG"; then
  rojo "Fallo el despliegue. Recursos con error:"
  aws cloudformation describe-stack-events --region "$REGION" --stack-name "$PILA" --max-items 30 \
    --query "StackEvents[?contains(ResourceStatus,'FAILED')].[LogicalResourceId,ResourceStatusReason]" --output table
  exit 1
fi

aws cloudformation describe-stacks --region "$REGION" --stack-name "$PILA" \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
azul "Esperando a que los 3 servicios de ECS queden estables..."
aws ecs wait services-stable --region "$REGION" --cluster "$PILA" \
  --services consentimiento perfilamiento mock-open-finance
verde "Listo. Siguiente paso: ./04-ec2.sh subir"
