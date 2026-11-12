#!/usr/bin/env bash
# EXP-010 - Crea o actualiza la pila de CloudFormation (Cognito, AWS API Gateway,
# ECS Fargate con los 4 servicios, ALB y RDS). Tarda ~15 min (casi todo es RDS).
#
#   ./02-desplegar.sh ClaveSegura123
source "$(dirname "$0")/00-config.sh"
DB_PASSWORD="${1:?Uso: ./02-desplegar.sh <clave-bd solo letras y numeros>}"
FLAG="${JWT_VALIDATION_ENABLED:-true}"
# AWS Academy tiene el rol LabRole; en una cuenta propia la plantilla crea sus roles.
if aws iam get-role --role-name LabRole >/dev/null 2>&1; then LABROLE=true; else LABROLE=false; fi

VPC="$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)"
subred() {
  aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC" "Name=availability-zone,Values=$1" \
    "Name=default-for-az,Values=true" --query 'Subnets[0].SubnetId' --output text
}
SUB_A="$(subred "${AWS_REGION}a")"
SUB_B="$(subred "${AWS_REGION}b")"
echo "VPC $VPC | subredes $SUB_A $SUB_B | JWT_VALIDATION_ENABLED=$FLAG | LabRole=$LABROLE"

if ! aws cloudformation deploy --stack-name "$PILA" \
  --template-file "$EXP_DIR/infra/exp010.yaml" \
  --parameter-overrides VpcId="$VPC" SubnetA="$SUB_A" SubnetB="$SUB_B" \
    DbPassword="$DB_PASSWORD" JwtValidationEnabled="$FLAG" UsarLabRole="$LABROLE" \
  --capabilities CAPABILITY_IAM; then
  echo "Fallo el despliegue. Eventos con error:"
  aws cloudformation describe-stack-events --stack-name "$PILA" --max-items 20 \
    --query "StackEvents[?contains(ResourceStatus,'FAILED')].[LogicalResourceId,ResourceStatusReason]" --output table
  exit 1
fi
aws cloudformation describe-stacks --stack-name "$PILA" \
  --query 'Stacks[0].Outputs[].[OutputKey,OutputValue]' --output table
echo "Listo. Espera a que los 4 servicios de ECS esten RUNNING y healthy (2-3 min)."
