# EXP-006 (H7.2.1) - Crea o actualiza la pila de CloudFormation del experimento.
# Busca sola la VPC por defecto y una subred en cada zona (a y b).
#
#   .\02-desplegar.ps1 -DbPassword "UnaClaveSegura123"                 # corridas con tacticas
#   .\02-desplegar.ps1 -DbPassword "UnaClaveSegura123" -Modo control   # prueba de control
#
# Cambiar de modo solo actualiza las tareas de ECS (no recrea las bases de datos).
param(
  [Parameter(Mandatory = $true)][string]$DbPassword,
  [ValidateSet("tacticas", "control")][string]$Modo = "tacticas",
  [string]$Region = "us-east-1",
  [string]$Pila = "solventa-exp006",
  [string]$ZonaA = "us-east-1a",
  [string]$ZonaB = "us-east-1b",
  [string]$ImageTag = "latest"
)
$ErrorActionPreference = "Stop"

$vpc = (aws ec2 describe-vpcs --region $Region --filters Name=isDefault,Values=true `
  --query "Vpcs[0].VpcId" --output text).Trim()
function Subred($zona) {
  (aws ec2 describe-subnets --region $Region `
    --filters Name=vpc-id,Values=$vpc Name=availability-zone,Values=$zona Name=default-for-az,Values=true `
    --query "Subnets[0].SubnetId" --output text).Trim()
}
$subA = Subred $ZonaA
$subB = Subred $ZonaB
if ($subA -eq "None" -or $subB -eq "None") { throw "No encontre subredes por defecto en $ZonaA / $ZonaB" }

$retry = if ($Modo -eq "tacticas") { "true" } else { "false" }
Write-Host "VPC $vpc | $ZonaA=$subA | $ZonaB=$subB | modo=$Modo (RETRY_IDEMPOTENCY_ENABLED=$retry)" -ForegroundColor Cyan

$plantilla = Join-Path $PSScriptRoot "..\infra\exp006.yaml"
aws cloudformation deploy --region $Region --stack-name $Pila --template-file $plantilla `
  --parameter-overrides VpcId=$vpc SubnetA=$subA SubnetB=$subB AzA=$ZonaA AzB=$ZonaB `
  DbPassword=$DbPassword RetryIdempotencyEnabled=$retry ImageTag=$ImageTag
if ($LASTEXITCODE -ne 0) {
  Write-Host "Fallo el despliegue. Eventos recientes:" -ForegroundColor Red
  aws cloudformation describe-stack-events --region $Region --stack-name $Pila --max-items 15 `
    --query "StackEvents[?contains(ResourceStatus,'FAILED')].[LogicalResourceId,ResourceStatusReason]" --output table
  exit 1
}

aws cloudformation describe-stacks --region $Region --stack-name $Pila `
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
Write-Host "Listo. Espera a que las tareas de ECS esten RUNNING antes de correr." -ForegroundColor Green
