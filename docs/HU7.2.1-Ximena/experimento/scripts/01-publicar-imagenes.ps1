# EXP-006 (H7.2.1) - Construye y publica en Amazon ECR las imagenes de los tres
# servicios del experimento: pagos, siniestros y pasarela-mock.
# Requisitos: Docker Desktop corriendo y credenciales del Learner Lab en
# ~/.aws/credentials (AWS Details > AWS CLI > copiar).
#
#   .\01-publicar-imagenes.ps1
param(
  [string]$Region = "us-east-1",
  [string]$Tag = "latest"
)
$ErrorActionPreference = "Stop"

$raiz = Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")
$cuenta = (aws sts get-caller-identity --query Account --output text).Trim()
$registro = "$cuenta.dkr.ecr.$Region.amazonaws.com"
Write-Host "Cuenta $cuenta - registro $registro" -ForegroundColor Cyan

aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $registro
if ($LASTEXITCODE -ne 0) { throw "No se pudo iniciar sesion en ECR" }

$servicios = @(
  @{ repo = "solventa-pagos";         carpeta = "services\pagos" },
  @{ repo = "solventa-siniestros";    carpeta = "services\siniestros" },
  @{ repo = "solventa-pasarela-mock"; carpeta = "services\pasarela-mock" }
)

foreach ($s in $servicios) {
  $repo = $s.repo
  aws ecr describe-repositories --repository-names $repo --region $Region 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Creando repositorio $repo" -ForegroundColor Yellow
    aws ecr create-repository --repository-name $repo --region $Region | Out-Null
  }
  $imagen = "$registro/${repo}:$Tag"
  Write-Host "Construyendo $imagen" -ForegroundColor Cyan
  # --platform: Fargate corre en x86_64 aunque el PC sea ARM
  docker build --platform linux/amd64 -t $imagen (Join-Path $raiz $s.carpeta)
  if ($LASTEXITCODE -ne 0) { throw "Fallo el build de $repo" }
  docker push $imagen
  if ($LASTEXITCODE -ne 0) { throw "Fallo el push de $repo" }
}
Write-Host "Imagenes publicadas." -ForegroundColor Green
