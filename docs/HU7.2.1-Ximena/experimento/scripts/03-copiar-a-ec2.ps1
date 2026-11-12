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
$ErrorActionPreference = "Continue"  # PowerShell 5.1 trata la salida de error de aws/docker como excepcion con "Stop"; se valida $LASTEXITCODE

# IP actual de la EC2 de carga (cambia cada vez que el Learner Lab la reinicia;
# la salida CargaIpPublica de la pila no se actualiza)
$ip = (aws ec2 describe-instances --region $Region `
  --filters "Name=tag:aws:cloudformation:stack-name,Values=$Pila" "Name=tag:aws:cloudformation:logical-id,Values=Carga" "Name=instance-state-name,Values=running" `
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
if ($LASTEXITCODE -ne 0 -or -not $ip -or $ip.Trim() -eq "None") { throw "No encontre la EC2 de carga encendida (credenciales vencidas o Lab apagado?)" }
$ip = $ip.Trim()
Write-Host "EC2 de carga: $ip" -ForegroundColor Cyan

if ($Traer) {
  $destino = Join-Path $PSScriptRoot "..\..\resultados"
  New-Item -ItemType Directory -Force -Path $destino | Out-Null
  scp -i $Llave -o StrictHostKeyChecking=no -r "ec2-user@${ip}:~/resultados/*" $destino
  if ($LASTEXITCODE -ne 0) { throw "Fallo la copia de resultados" }
  Write-Host "Resultados copiados en $destino" -ForegroundColor Green
} else {
  $carga = Join-Path $PSScriptRoot "..\carga"
  scp -i $Llave -o StrictHostKeyChecking=no -r $carga "ec2-user@${ip}:~/"
  if ($LASTEXITCODE -ne 0) { throw "Fallo la copia de scripts a la EC2" }
  ssh -i $Llave -o StrictHostKeyChecking=no "ec2-user@$ip" "sed -i 's/\r$//' ~/carga/*.sh ~/carga/*.py && chmod +x ~/carga/*.sh"
  Write-Host "Scripts copiados. Conectate con: ssh -i $Llave ec2-user@$ip" -ForegroundColor Green
}
