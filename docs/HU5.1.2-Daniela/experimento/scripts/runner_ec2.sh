#!/bin/bash
# EXP-008: corre en la EC2 de JMeter (rol LabRole) para que las corridas largas
# no dependan de la sesion de quien las lanza. Se invoca por SSM:
#
#   runner_ec2.sh imagenes        build y push de las 3 imagenes a ECR
#   runner_ec2.sh sembrar         10.000 perfiles por POST /perfiles
#   runner_ec2.sh humo            1 min a 5 peticiones/s por socio
#   runner_ec2.sh calibrar HASTA [DESDE] [PASO] [NOMBRE]  escalones de 2 min sin cuota
#   runner_ec2.sh corridas C [DESDE]  6 corridas alternadas sin/con cuota de 14 min
#   runner_ec2.sh demo C          una corrida con cuota (para grabar el video)
#
# Variables en /opt/exp008/env.sh: B, ALB, INT, COT_DB, PERF_DB, REDIS,
# PGPASSWORD, REG, CLUSTER, TD_SIN y TD_CON (task definitions del gateway).
set -uo pipefail
source /opt/exp008/env.sh
cd /opt/exp008
mkdir -p res
CARGA=src/docs/HU5.1.2-Daniela/experimento/carga

progreso() {
  echo "$(date -u +%FT%TZ) $*" | tee -a res/progreso.log
  aws s3 cp res/progreso.log "s3://$B/res/progreso.log" --quiet
}

imagenes() {
  aws s3 cp "s3://$B/codigo.tgz" . --quiet && rm -rf src && mkdir src && tar xzf codigo.tgz -C src
  aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$REG" >/dev/null
  for s in api-gateway cotizacion perfilamiento; do
    docker build -q -t "$REG/exp008-$s:exp008" "src/services/$s" && docker push -q "$REG/exp008-$s:exp008" \
      && progreso "imagen $s publicada" || { progreso "ERROR imagen $s"; return 1; }
  done
}

sembrar() {
  progreso "sembrando perfiles"
  progreso "siembra: $(python3 $CARGA/sembrar_perfiles.py "http://$INT:8002" 10000)"
}

esperar_estable() {
  aws ecs wait services-stable --cluster "$CLUSTER" --services api-gateway cotizacion perfilamiento
  for i in $(seq 60); do curl -sf "http://$ALB/health" >/dev/null && break; sleep 5; done
  sleep 30   # que el ALB termine de marcar sanos los destinos
}

# Reinicio limpio entre corridas: tabla de cotizaciones vacia, Redis vacio y
# las tres tareas nuevas. El gateway arranca con la task definition pedida
# (con o sin cuota).
reinicio() {
  local td=$1
  psql -h "$COT_DB" -U postgres -d cotizacion_db -qc 'TRUNCATE cotizaciones' || true
  redis6-cli -h "$REDIS" FLUSHALL >/dev/null
  aws ecs update-service --cluster "$CLUSTER" --service api-gateway --task-definition "$td" \
    --force-new-deployment --query service.taskDefinition --output text >/dev/null
  for s in cotizacion perfilamiento; do
    aws ecs update-service --cluster "$CLUSTER" --service "$s" --force-new-deployment \
      --query service.status --output text >/dev/null
  done
  sleep 20
  esperar_estable
  local r
  r=$(curl -s -o /dev/null -w '%{http_code}' -X POST "http://$ALB/v1/cotizaciones" \
      -H 'content-type: application/json' -H 'x-api-key: exp008-prueba' \
      -d '{"clienteId":"00000000-0000-4000-8000-100000000001","productoId":"22222222-2222-2222-2222-222222222222"}')
  progreso "reinicio listo con $(basename "$td"), cotizacion de prueba HTTP $r"
}

correr_jmeter() {
  local nombre=$1 tipo=$2; shift 2
  python3 $CARGA/generar_plan.py "$tipo" "$@" --salida "res/$nombre.jmx" >/dev/null
  rm -f "res/$nombre.jtl"
  progreso "inicio $nombre"
  date -u +%FT%TZ > "res/$nombre.inicio"
  HEAP="-Xms1g -Xmx4g" jmeter -n -t "res/$nombre.jmx" -Jhost="$ALB" -Jport=80 -l "res/$nombre.jtl" \
    -j "res/$nombre.log" -Jjmeter.save.saveservice.output_format=csv > "res/$nombre.out" 2>&1
  date -u +%FT%TZ > "res/$nombre.fin"
  gzip -kf "res/$nombre.jtl"
  for f in "$nombre.jtl.gz" "$nombre.jmx" "$nombre.inicio" "$nombre.fin" "$nombre.out"; do
    aws s3 cp "res/$f" "s3://$B/res/$f" --quiet
  done
  progreso "fin $nombre ($(($(wc -l < "res/$nombre.jtl") - 1)) muestras)"
}

case "${1:-}" in
  imagenes) imagenes ;;
  sembrar) sembrar ;;
  humo) reinicio "$TD_SIN"; correr_jmeter humo humo --rps 5 ;;
  calibrar)  # calibrar HASTA [DESDE] [PASO] [NOMBRE]
    reinicio "$TD_SIN"
    correr_jmeter "${5:-calibracion}" calibracion --desde "${3:-20}" --paso "${4:-20}" --hasta "${2:-200}" ;;
  corridas)
    for spec in 1:sin 2:con 3:sin 4:con 5:sin 6:con; do   # corridas C [DESDE]
      n=${spec%%:*}; m=${spec##*:}
      [ "$n" -lt "${3:-1}" ] && continue
      if [ "$m" = con ]; then td=$TD_CON; else td=$TD_SIN; fi
      reinicio "$td"
      correr_jmeter "corrida_${n}_${m}" corrida --c "$2"
    done
    progreso "FIN de las 6 corridas" ;;
  demo) reinicio "$TD_CON"; correr_jmeter demo_video corrida --c "$2" ;;   # una corrida con cuota para el video
  *) echo "uso: $0 imagenes|sembrar|humo|calibrar HASTA [DESDE] [PASO] [NOMBRE]|corridas C [DESDE]|demo C"; exit 1 ;;
esac
