#!/usr/bin/env bash
# EXP-007 · Paso 2: crea el certificado autofirmado para el HTTPS del ALB, lo importa
# en AWS (ACM; si el laboratorio no lo deja, en IAM) y genera el secreto del JWT.
# Todo queda en ~/exp007 (fuera del repo: ahi hay una llave privada).
#
#   ./02-certificado-y-secretos.sh
source "$(dirname "$0")/comun.sh"
verificar_credenciales
mkdir -p "$SECRETOS"
cd "$SECRETOS" || exit 1

if [ ! -f cert.pem ]; then
  azul "Generando certificado autofirmado (30 dias)"
  # El ALB exige un nombre de dominio completo (FQDN). Se usa el comodin del DNS que
  # AWS asigna a los ALB de us-east-1, asi el nombre ademas coincide con el del ALB.
  openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 30 \
    -keyout key.pem -out cert.pem -subj "/CN=*.us-east-1.elb.amazonaws.com" 2>/dev/null
  chmod 600 key.pem
fi

if [ ! -f jwt_secret.txt ]; then
  openssl rand -hex 32 > jwt_secret.txt
  chmod 600 jwt_secret.txt
fi

if [ -s cert_arn.txt ]; then
  verde "Ya habia un certificado importado: $(cat cert_arn.txt)"
  exit 0
fi

azul "Importando el certificado en ACM"
if arn=$(aws acm import-certificate --region "$REGION" \
      --certificate fileb://cert.pem --private-key fileb://key.pem \
      --tags Key=exp,Value=exp007 --query CertificateArn --output text 2>/tmp/exp007-acm.err); then
  echo "$arn" > cert_arn.txt
  verde "Certificado en ACM: $arn"
else
  rojo "ACM no lo permitio ($(head -1 /tmp/exp007-acm.err)). Probando con IAM..."
  arn=$(aws iam upload-server-certificate --server-certificate-name solventa-exp007 \
        --certificate-body file://cert.pem --private-key file://key.pem \
        --query ServerCertificateMetadata.Arn --output text)
  echo "$arn" > cert_arn.txt
  verde "Certificado en IAM: $arn"
fi
verde "Secretos en $SECRETOS (cert.pem, key.pem, jwt_secret.txt, cert_arn.txt)"
