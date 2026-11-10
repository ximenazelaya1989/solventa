# EXP-006 (H7.2.1) - Copia los scripts de carga a la EC2 y, al terminar,
# trae de vuelta los resultados a docs\HU7.2.1-Ximena\resultados.
# La llave labsuser.pem se descarga del Learner Lab (AWS Details > Download PEM).
#
#   .\03-copiar-a-ec2.ps1 -Llave C:\Users\ximen\Downloads\labsuser.pem            # subir scripts
#   .\03-copiar-a-ec2.ps1 -Llave C:\Users\ximen\Downloads\labsuser.pem -Traer     # bajar resultados
param(
  [Parameter(Mandatory = $true)][string]$Llave,
  [switch]$Traer,
  [string]$Region = "us-east-1",
  [string]$Pila = "solventa-exp006"
)
$ErrorActionPreference = "Stop"

$ip = (aws cloudformation describe-stacks --region $Region --stack-name $Pila `
  --query "Stacks[0].Outputs[?OutputKey=='CargaIpPublica'].OutputValue" --output text).Trim()
Write-Host "EC2 de carga: $ip" -ForegroundColor Cyan

if ($Traer) {
  $destino = Join-Path $PSScriptRoot "..\..\resultados"
  New-Item -ItemType Directory -Force -Path $destino | Out-Null
  scp -i $Llave -o StrictHostKeyChecking=no -r "ec2-user@${ip}:~/resultados/*" $destino
  Write-Host "Resultados copiados en $destino" -ForegroundColor Green
} else {
  $carga = Join-Path $PSScriptRoot "..\carga"
  scp -i $Llave -o StrictHostKeyChecking=no -r $carga "ec2-user@${ip}:~/"
  ssh -i $Llave -o StrictHostKeyChecking=no "ec2-user@$ip" "sed -i 's/\r$//' ~/carga/*.sh ~/carga/*.py && chmod +x ~/carga/*.sh"
  Write-Host "Scripts copiados. Conectate con: ssh -i $Llave ec2-user@$ip" -ForegroundColor Green
}
