#!/usr/bin/env bash
set -euo pipefail

mode="${1:-}"
if [[ "$mode" != "vertical" && "$mode" != "horizontal" ]]; then
  echo "Uso: npm run experiment:h431 -- vertical|horizontal"
  exit 2
fi

command -v docker >/dev/null || { echo "Falta Docker."; exit 1; }
if command -v k6 >/dev/null; then
  k6_mode="local"
else
  k6_mode="docker"
fi

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
experiment_dir="$root_dir/experiments/h4.3.1"
compose_file="$experiment_dir/compose.$mode.yml"
result_dir="$experiment_dir/results/$mode/$(date -u +%Y%m%dT%H%M%SZ)"
result_relative="results/${mode}/$(basename "$result_dir")"
mkdir -p "$result_dir"

{
  echo "commit=$(git -C "$root_dir" rev-parse HEAD)"
  echo "mode=$mode"
  echo "rates=${RATES:-200 500 800 1100 1400}"
  echo "duration=${DURATION:-2m}"
  echo "api_cpus=${API_CPUS:-3.0}"
  echo "api_memory=${API_MEMORY:-3g}"
  echo "instance_cpus=${INSTANCE_CPUS:-1.0}"
  echo "instance_memory=${INSTANCE_MEMORY:-1g}"
  echo "db_cpus=${DB_CPUS:-2.0}"
  echo "db_memory=${DB_MEMORY:-2g}"
  echo "k6_mode=$k6_mode"
} > "$result_dir/configuration.txt"

cleanup() {
  docker compose -p "h431-$mode" -f "$compose_file" down -v
}
trap cleanup EXIT

docker compose -p "h431-$mode" -f "$compose_file" up -d --build
until curl --fail --silent http://localhost:8080/ >/dev/null; do sleep 2; done

run_offset=0
failed=0
for rate in ${RATES:-200 500 800 1100 1400}; do
  echo "Ejecutando nivel de carga: $rate TPS"
  level_failed=0
  if [[ "$k6_mode" == "local" ]]; then
    env BASE_URL="${BASE_URL:-http://localhost:8080}" \
      RATE="$rate" DURATION="${DURATION:-2m}" \
      RUN_OFFSET="$run_offset" \
      SUMMARY_FILE="$result_dir/summary-$rate-tps.json" \
      k6 run "$experiment_dir/k6/reprocesamiento.js" || level_failed=1
  else
    docker run --rm \
      -e BASE_URL="${BASE_URL:-http://host.docker.internal:8080}" \
      -e RATE="$rate" -e DURATION="${DURATION:-2m}" \
      -e RUN_OFFSET="$run_offset" \
      -e PRE_ALLOCATED_VUS="${PRE_ALLOCATED_VUS:-300}" \
      -e MAX_VUS="${MAX_VUS:-2000}" \
      -e SUMMARY_FILE="/work/$result_relative/summary-$rate-tps.json" \
      -v "$experiment_dir:/work" -w /work grafana/k6:latest \
      run /work/k6/reprocesamiento.js || level_failed=1
  fi
  if [[ "$level_failed" -ne 0 ]]; then
    failed=1
    echo "El nivel $rate TPS no cumplió uno o más umbrales; se continúa para conservar la curva completa."
  fi
  run_offset=$((run_offset + 100000000))
done

docker compose -p "h431-$mode" -f "$compose_file" logs --no-color > "$result_dir/containers.log"
echo "Evidencia guardada en $result_dir"
exit "$failed"
