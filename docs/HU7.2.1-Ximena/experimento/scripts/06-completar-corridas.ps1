# EXP-006 (H7.2.1) - Completa las corridas que faltan del diseno (3 con tacticas y 3 de control)
# con un solo comando, en una sesion nueva del Learner Lab.
#
#   .\06-completar-corridas.ps1 -DbPassword "TuClave" -Llave C:\Users\ximen\Downloads\labsuser.pem
#   .\06-completar-corridas.ps1 -Llave C:\Users\ximen\Downloads\labsuser.pem -Ver     # ver avance
#
# Que hace:
#   0. Espera a que la EC2 de carga, Aurora y la pila esten listas (tras reiniciar el Lab).
#   1. Corre en el modo actual las corridas que faltan de ese modo (por defecto control-3),
#      esperando a que terminen (~20 min por corrida; deja esta ventana abierta).
#   2. Cambia al otro modo y deja corriendo en segundo plano las que faltan (tacticas-2 y
#      tacticas-3) mas la tabla comparativa. Esa parte sigue aunque cierres la ventana.
param(
  [string]$DbPassword,
  [Parameter(Mandatory = $true)][string]$Llave,
  [string[]]$Control = @("control-3"),
  [string[]]$Tacticas = @("tacticas-2", "tacticas-3"),
  [switch]$Ver,
  [string]$Region = "us-east-1",
  [string]$Pila = "solventa-exp006"
)
$ErrorActionPreference = "Continue"  # se valida $LASTEXITCODE

function IpCarga {
  for ($i = 0; $i -lt 30; $i++) {
    $ip = aws ec2 describe-instances --region $Region `
      --filters "Name=tag:aws:cloudformation:stack-name,Values=$Pila" "Name=tag:aws:cloudformation:logical-id,Values=Carga" "Name=instance-state-name,Values=running" `
      --query "Reservations[0].Instances[0].PublicIpAddress" --output text
    if ($LASTEXITCODE -eq 0 -and $ip -and $ip.Trim() -ne "None") { return $ip.Trim() }
    Write-Host "  esperando a que la EC2 de carga este encendida..."; Start-Sleep 20
  }
  throw "La EC2 de carga no esta encendida (credenciales vencidas o Lab apagado?)"
}
$ip = IpCarga
$ssh = @("-i", $Llave, "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "ec2-user@$ip")

if ($Ver) { ssh @ssh "tail -n 25 ~/completar.log"; exit 0 }
if (-not $DbPassword) { throw "Falta -DbPassword (la misma clave con la que desplegaste)" }

Write-Host "EC2 de carga: $ip" -ForegroundColor Cyan

# 0. Estado de la pila (si quedo a medias por el corte del Lab, se completa el rollback)
$estado = (aws cloudformation describe-stacks --region $Region --stack-name $Pila --query "Stacks[0].StackStatus" --output text).Trim()
Write-Host "Pila: $estado"
if ($estado -eq "UPDATE_ROLLBACK_FAILED") {
  aws cloudformation continue-update-rollback --region $Region --stack-name $Pila
  $estado = "UPDATE_ROLLBACK_IN_PROGRESS"
}
while ($estado -like "*IN_PROGRESS*") {
  Start-Sleep 20
  $estado = (aws cloudformation describe-stacks --region $Region --stack-name $Pila --query "Stacks[0].StackStatus" --output text).Trim()
  Write-Host "  pila: $estado"
}

# Aurora disponible
$cluster = (aws cloudformation describe-stacks --region $Region --stack-name $Pila `
  --query "Stacks[0].Outputs[?OutputKey=='AuroraCluster'].OutputValue" --output text).Trim()
do {
  $st = (aws rds describe-db-clusters --region $Region --db-cluster-identifier $cluster --query "DBClusters[0].Status" --output text).Trim()
  if ($st -eq "stopped") { aws rds start-db-cluster --region $Region --db-cluster-identifier $cluster | Out-Null }
  if ($st -ne "available") { Write-Host "  Aurora: $st (esperando)"; Start-Sleep 30 }
} while ($st -ne "available")

# Modo actual (segun la tarea de Siniestros desplegada)
$modo = ssh @ssh "source ~/exp006.env && aws ecs describe-task-definition --task-definition `$(aws ecs describe-services --cluster `$ECS_CLUSTER --services siniestros --query 'services[0].taskDefinition' --output text) --query 'taskDefinition.containerDefinitions[0].environment' --output text | grep RETRY_IDEMPOTENCY_ENABLED | grep -o 'true\|false'"
$modo = "$modo".Trim()
Write-Host "Modo actual: RETRY_IDEMPOTENCY_ENABLED=$modo" -ForegroundColor Cyan
if ($modo -eq "true") { $ahora = $Tacticas; $despues = $Control; $otro = "control" }
else                  { $ahora = $Control;  $despues = $Tacticas; $otro = "tacticas" }

function Lista($nombres) { ($nombres | ForEach-Object { "./ejecutar_corrida.sh $_" }) -join " && sleep 180 && " }
$espera = "aws ecs wait services-stable --cluster `$ECS_CLUSTER --services pagos siniestros && sleep 60"

# 1. Corridas en el modo actual (en primer plano)
if ($ahora.Count -gt 0) {
  Write-Host "1/2 Corriendo $($ahora -join ', ') en el modo actual (~$(20 * $ahora.Count) min). No cierres esta ventana." -ForegroundColor Cyan
  ssh @ssh "cd ~/carga && source ~/exp006.env && $espera && $(Lista $ahora) 2>&1 | tee -a ~/completar.log | grep --line-buffered -E 'Corrida|Listo|H1|Disponibilidad'"
}

# 2. Cambio de modo y corridas restantes (en segundo plano)
if ($despues.Count -gt 0) {
  Write-Host "2/2 Cambiando a modo $otro..." -ForegroundColor Cyan
  & (Join-Path $PSScriptRoot "02-desplegar.ps1") -DbPassword $DbPassword -Modo $otro -Region $Region -Pila $Pila
  if ($LASTEXITCODE -ne 0) { throw "Fallo el cambio a modo $otro" }
  $remoto = "cd ~/carga && source ~/exp006.env && $espera && $(Lista $despues) && python3 comparar.py ~/resultados"
  ssh @ssh "nohup bash -c '$remoto' >> ~/completar.log 2>&1 < /dev/null &"
  if ($LASTEXITCODE -ne 0) { throw "No se pudo lanzar en la EC2" }
  Write-Host "Lanzadas $($despues -join ', ') en segundo plano (~$(5 + 20 * $despues.Count) min). Puedes cerrar esta ventana." -ForegroundColor Green
}
Write-Host "Ver avance:   .\06-completar-corridas.ps1 -Llave $Llave -Ver"
Write-Host "Al terminar:  .\03-copiar-a-ec2.ps1 -Llave $Llave -Traer   y luego   .\04-eliminar.ps1"
