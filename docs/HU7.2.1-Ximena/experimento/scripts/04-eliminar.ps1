# EXP-006 (H7.2.1) - Borra toda la infraestructura del experimento para no gastar
# creditos (Aurora, RDS, ECS, ALBs, EC2). Las imagenes de ECR se conservan
# (ocupan centavos); con -ConImagenes tambien se borran los repositorios.
#
#   .\04-eliminar.ps1
#   .\04-eliminar.ps1 -ConImagenes
param(
  [string]$Region = "us-east-1",
  [string]$Pila = "solventa-exp006",
  [switch]$ConImagenes
)
$ErrorActionPreference = "Stop"

Write-Host "Eliminando la pila $Pila (tarda unos 10-15 minutos)..." -ForegroundColor Yellow
aws cloudformation delete-stack --region $Region --stack-name $Pila
aws cloudformation wait stack-delete-complete --region $Region --stack-name $Pila
Write-Host "Pila eliminada." -ForegroundColor Green

if ($ConImagenes) {
  foreach ($repo in "solventa-pagos", "solventa-siniestros", "solventa-pasarela-mock") {
    aws ecr delete-repository --region $Region --repository-name $repo --force | Out-Null
    Write-Host "Repositorio $repo eliminado"
  }
}
