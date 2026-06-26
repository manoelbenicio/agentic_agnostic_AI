#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/common.sh"

require_cmd docker
require_cmd curl
require_cmd lsof
require_cmd ss
require_cmd npm
require_cmd setsid
load_aop_env

log "starting AOP base services"
docker_compose_aop up -d
wait_until "postgres" 60 2 docker_compose_aop exec -T postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
wait_until "redis" 60 2 docker_compose_aop exec -T redis redis-cli ping

log "starting HerdMaster observability stack"
docker_compose_obs up -d
wait_observability_http_200 "prometheus" "http://127.0.0.1:9090/-/healthy"
wait_observability_http_200 "grafana" "http://127.0.0.1:3000/api/health"
wait_observability_http_200 "alertmanager" "http://127.0.0.1:9093/-/ready"
wait_observability_http_200 "blackbox-exporter" "http://127.0.0.1:9115/-/healthy"
wait_observability_http_200 "remediation-webhook" "http://127.0.0.1:9099/health"

write_herdmaster_config
if [[ "$(http_code http://127.0.0.1:8080/metrics -H "$(herdmaster_auth_header)")" == "200" ]]; then
  log "HerdMaster already healthy on :8080"
  record_listener_pid "HerdMaster" "${HERDMASTER_PORT}" "${HERDMASTER_PID_FILE}"
else
  kill_port_processes "HerdMaster" "${HERDMASTER_PORT}"
  log "starting HerdMaster control plane on :8080"
  (
    cd "${HERDMASTER_DIR}"
    setsid env DATABASE_URL="${DATABASE_URL}" PYTHONPATH="${HERDMASTER_DIR}/src" \
      herdmaster start --http --config "${HERDMASTER_CONFIG}" \
      >>"${LOG_DIR}/herdmaster.log" 2>&1 < /dev/null &
    printf '%s\n' "$!" > "${HERDMASTER_PID_FILE}"
  )
  wait_http_200 "HerdMaster" "http://127.0.0.1:8080/metrics" -H "$(herdmaster_auth_header)"
  record_listener_pid "HerdMaster" "${HERDMASTER_PORT}" "${HERDMASTER_PID_FILE}"
fi

if [[ "$(http_code http://127.0.0.1:8090/health)" == "200" ]] && aop_control_plane_coupling_connected; then
  log "AOP control-plane already healthy on :8090 with HerdMaster coupling connected"
  record_listener_pid "AOP control-plane" "${AOP_API_PORT}" "${AOP_API_PID_FILE}"
else
  kill_port_processes "AOP control-plane" "${AOP_API_PORT}"
  log "starting AOP control-plane on :8090 with HerdMaster token from runtime config"
  (
    cd "${ROOT_DIR}"
    export HERDMASTER_TOKEN
    HERDMASTER_TOKEN="$(herdmaster_token)"
    setsid env DATABASE_URL="${DATABASE_URL}" REDIS_URL="${REDIS_URL}" HERDMASTER_URL="http://127.0.0.1:8080" \
      HERDMASTER_TOKEN="${HERDMASTER_TOKEN}" \
      PYTHONPATH="${AOP_DIR}/control-plane:${HERDMASTER_DIR}/src" \
      "$(uvicorn_bin)" app.main:app --host 127.0.0.1 --port 8090 \
      >>"${LOG_DIR}/aop-control-plane.log" 2>&1 < /dev/null &
    printf '%s\n' "$!" > "${AOP_API_PID_FILE}"
  )
  wait_http_200 "AOP control-plane" "http://127.0.0.1:8090/health"
  wait_http_200 "AOP readiness" "http://127.0.0.1:8090/health/ready"
  record_listener_pid "AOP control-plane" "${AOP_API_PORT}" "${AOP_API_PID_FILE}"
fi

if [[ "$(http_code http://127.0.0.1:13000)" == "200" ]]; then
  log "AOP frontend already healthy on :13000"
  record_listener_pid "AOP frontend" "${AOP_WEB_PORT}" "${AOP_WEB_PID_FILE}"
else
  kill_port_processes "AOP frontend" "${AOP_WEB_PORT}"
  log "starting AOP frontend on :13000"
  (
    cd "${AOP_DIR}/web"
    setsid env NEXT_PUBLIC_API_URL="http://127.0.0.1:8090" npm run dev -- --hostname 127.0.0.1 --port 13000 \
      >>"${LOG_DIR}/aop-frontend.log" 2>&1 < /dev/null &
    printf '%s\n' "$!" > "${AOP_WEB_PID_FILE}"
  )
  wait_http_200 "AOP frontend" "http://127.0.0.1:13000"
  record_listener_pid "AOP frontend" "${AOP_WEB_PORT}" "${AOP_WEB_PID_FILE}"
fi

print_status_table
