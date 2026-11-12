# EXP-006 (H7.2.1) - Prueba de control completa con un solo comando.
#   1. Cambia las tareas de ECS a modo control (RETRY_IDEMPOTENCY_ENABLED=false)
#   2. Entra a la EC2 de carga y deja corriendo, en segundo plano, control-1 y
#      control-2 (y la tabla comparativa). Sigue corriendo aunque cierres la ventana.
#
#   .\05-correr-control.ps1 -DbPassword "TuClave" -Llave C:\Users\ximen\Downloads\labsuser.pem
#   .\05-correr-control.ps1 -DbPassword "TuClave" -Llave ... -Corridas 1     # solo control-1
#
# Para ver el avance:   .\05-correr-control.ps1 -Llave ... -Ver
param(
  [string]$DbPassword,
  [Parameter(Mandatory = $true)][string]$Llave,
  [int]$Corridas = 2,
  [switch]$Ver,
  [string]$Region = "us-east-1",
  [string]$Pila = "solventa-exp006"
)
$ErrorActionPreference = "Continue"  # se valida $LASTEXITCODE

# IP actual de la EC2 de carga (cambia cada vez que el Learner Lab la reinicia;
# la salida CargaIpPublica de la pila no se actualiza)
$ip = (aws ec2 describe-instances --region $Region `
  --filters "Name=tag:aws:cloudformation:stack-name,Values=$Pila" "Name=tag:aws:cloudformation:logical-id,Values=Carga" "Name=instance-state-name,Values=running" `
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
if ($LASTEXITCODE -ne 0 -or -not $ip -or $ip.Trim() -eq "None") { throw "No encontre la EC2 de carga encendida (credenciales vencidas o Lab apagado?)" }
$ip = $ip.Trim()
$ssh = @("-i", $Llave, "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "ec2-user@$ip")

if ($Ver) {
  ssh @ssh "tail -n 25 ~/control.log"
  exit 0
}
if (-not $DbPassword) { throw "Falta -DbPassword (la misma clave con la que desplegaste)" }

Write-Host "1/2 Cambiando a modo control..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "02-desplegar.ps1") -DbPassword $DbPassword -Modo control -Region $Region -Pila $Pila
if ($LASTEXITCODE -ne 0) { throw "Fallo el cambio a modo control" }

$lista = (1..$Corridas | ForEach-Object { "./ejecutar_corrida.sh control-$_" }) -join " && sleep 180 && "
$remoto = "cd ~/carga && source ~/exp006.env && aws ecs wait services-stable --cluster `$ECS_CLUSTER --services pagos siniestros && sleep 60 && $lista && python3 comparar.py ~/resultados"
Write-Host "2/2 Lanzando las corridas en la EC2 ($ip) en segundo plano..." -ForegroundColor Cyan
ssh @ssh "nohup bash -c '$remoto' > ~/control.log 2>&1 < /dev/null &"
if ($LASTEXITCODE -ne 0) { throw "No se pudo lanzar en la EC2" }

$min = 5 + 20 * $Corridas
Write-Host "Listo. Las corridas tardan unos $min min y siguen aunque cierres esta ventana." -ForegroundColor Green
Write-Host "Ver avance:      .\05-correr-control.ps1 -Llave $Llave -Ver"
Write-Host "Al terminar:     .\03-copiar-a-ec2.ps1 -Llave $Llave -Traer"
