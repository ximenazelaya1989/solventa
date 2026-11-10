#!/usr/bin/env bash
# EXP-006 (H7.2.1) - Inyeccion de fallas durante la corrida.
#   minuto 5  (T_PAGOS):  caida abrupta de una replica de Pagos (SIGKILL al proceso)
#   minuto 10 (T_AURORA): conmutacion por error de Aurora (failover-db-cluster)
# Registra el instante exacto de cada inyeccion (t0) en UTC con milisegundos,
# con el mismo reloj (Amazon Time Sync) que la sonda.
#
#   ./inyectar_fallas.sh inyecciones.csv
set -euo pipefail
source ~/exp006.env

SALIDA=${1:?uso: inyectar_fallas.sh <salida.csv>}
T_PAGOS=${T_PAGOS:-300}
T_AURORA=${T_AURORA:-600}
ahora() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }

echo "ts_utc,evento,detalle" > "$SALIDA"
inicio=$(date +%s)
esperar_hasta() { local s=$(( $1 - ($(date +%s) - inicio) )); (( s > 0 )) && sleep "$s"; true; }

# --- 1. Caida abrupta de una replica de Pagos ------------------------------
esperar_hasta "$T_PAGOS"
TAREA=$(aws ecs list-tasks --cluster "$ECS_CLUSTER" --service-name pagos \
  --desired-status RUNNING --query 'taskArns[0]' --output text)
IP=$(aws ecs describe-tasks --cluster "$ECS_CLUSTER" --tasks "$TAREA" \
  --query "tasks[0].attachments[0].details[?name=='privateIPv4Address'].value" --output text)
AZ=$(aws ecs describe-tasks --cluster "$ECS_CLUSTER" --tasks "$TAREA" \
  --query 'tasks[0].availabilityZone' --output text)
echo "$(ahora),caida_pagos,${IP}@${AZ}" >> "$SALIDA"
curl -s -m 3 -X POST -H "X-Fault-Token: $FAULT_TOKEN" "http://$IP:3000/admin/fallas/caida" || true
echo
echo "[$(ahora)] replica de Pagos $IP ($AZ) derribada"

# --- 2. Conmutacion por error de Aurora -------------------------------------
esperar_hasta "$T_AURORA"
ESCRITORA=$(aws rds describe-db-clusters --db-cluster-identifier "$AURORA_CLUSTER" \
  --query 'DBClusters[0].DBClusterMembers[?IsClusterWriter==`true`].DBInstanceIdentifier' --output text)
echo "$(ahora),failover_aurora,escritora_previa=$ESCRITORA" >> "$SALIDA"
aws rds failover-db-cluster --db-cluster-identifier "$AURORA_CLUSTER" > /dev/null
echo "[$(ahora)] failover de Aurora iniciado (escritora previa: $ESCRITORA)"
