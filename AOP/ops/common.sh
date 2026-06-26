#!/usr/bin/env bash
set -euo pipefail

OPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AOP_DIR="$(cd "${OPS_DIR}/.." && pwd)"
ROOT_DIR="$(cd "${AOP_DIR}/.." && pwd)"
HERDMASTER_DIR="${ROOT_DIR}/HerdMaster"

RUN_DIR="${AOP_OPS_RUN_DIR:-/tmp/aop-ops-run}"
LOG_DIR="${OPS_DIR}/logs"
RUNTIME_DIR="${AOP_OPS_RUNTIME_DIR:-/tmp/aop-ops-runtime}"
mkdir -p "${RUN_DIR}" "${LOG_DIR}" "${RUNTIME_DIR}"
chmod 700 "${RUN_DIR}" "${RUNTIME_DIR}" 2>/dev/null || true

AOP_DEPLOY_DIR="${AOP_DIR}/deploy"
AOP_ENV_FILE="${AOP_DEPLOY_DIR}/.env"
AOP_COMPOSE="${AOP_DEPLOY_DIR}/docker-compose.yml"
OBS_DIR="${HERDMASTER_DIR}/deploy/observability"
OBS_COMPOSE="${OBS_DIR}/docker-compose.yml"

HERDMASTER_CONFIG="${RUNTIME_DIR}/herdmaster.config.toml"
HERDMASTER_TOKEN_FILE="${RUNTIME_DIR}/herdmaster.token"
HERDMASTER_PID_FILE="${RUN_DIR}/herdmaster.pid"
AOP_API_PID_FILE="${RUN_DIR}/aop-control-plane.pid"
AOP_WEB_PID_FILE="${RUN_DIR}/aop-frontend.pid"

LOCAL_HOST="127.0.0.1"
POSTGRES_PORT="5432"
REDIS_PORT="6379"
HERDMASTER_PORT="8080"
AOP_API_PORT="8090"
AOP_WEB_PORT="13000"

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

warn() {
  printf '[%s] WARN: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2
}

die() {
  printf '[%s] ERROR: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

load_aop_env() {
  [[ -f "${AOP_ENV_FILE}" ]] || die "missing ${AOP_ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${AOP_ENV_FILE}"
  set +a
  : "${POSTGRES_USER:?POSTGRES_USER missing}"
  : "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD missing}"
  : "${POSTGRES_DB:?POSTGRES_DB missing}"
  export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${LOCAL_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
  export REDIS_URL="redis://${LOCAL_HOST}:${REDIS_PORT}/0"
}

docker_compose_aop() {
  docker compose --env-file "${AOP_ENV_FILE}" -f "${AOP_COMPOSE}" "$@"
}

docker_compose_obs() {
  docker compose -f "${OBS_COMPOSE}" "$@"
}

observability_network_mode() {
  local mode
  mode="$(docker_compose_obs config 2>/dev/null | awk '
    $1 == "network_mode:" {
      gsub(/"/, "", $2)
      print $2
    }
  ' | sort -u | tr '\n' ' ')"
  if [[ "${mode}" == *host* ]]; then
    printf '%s\n' "host"
  else
    printf '%s\n' "published"
  fi
}

http_code() {
  local url="$1"
  shift || true
  curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$@" "${url}" 2>/dev/null || true
}

wait_until() {
  local name="$1"
  local attempts="$2"
  local sleep_s="$3"
  shift 3
  local i
  for ((i = 1; i <= attempts; i++)); do
    if "$@" >/dev/null 2>&1; then
      log "${name}: healthy"
      return 0
    fi
    log "${name}: waiting (${i}/${attempts})"
    sleep "${sleep_s}"
  done
  return 1
}

wait_http_200() {
  local name="$1"
  local url="$2"
  shift 2
  local i
  local code
  for ((i = 1; i <= 60; i++)); do
    code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$@" "${url}" 2>/dev/null || true)"
    if [[ "${code}" == "200" ]]; then
      log "${name}: healthy"
      return 0
    fi
    log "${name}: waiting (${i}/60, http=${code:-none})"
    sleep 2
  done
  return 1
}

wait_observability_http_200() {
  local name="$1"
  local url="$2"
  local mode
  mode="$(observability_network_mode)"
  log "${name}: observability probe mode=${mode} url=${url}"
  wait_http_200 "${name}" "${url}"
}

port_listening() {
  local port="$1"
  ss -ltn "sport = :${port}" 2>/dev/null | grep -q ":${port}"
}

pid_alive() {
  local pid="$1"
  [[ -n "${pid}" ]] && kill -0 "${pid}" >/dev/null 2>&1
}

pid_from_file() {
  local file="$1"
  [[ -f "${file}" ]] || return 1
  local pid
  pid="$(tr -dc '0-9' < "${file}")"
  [[ -n "${pid}" ]] || return 1
  printf '%s\n' "${pid}"
}

stop_pid_file() {
  local label="$1"
  local file="$2"
  local pid=""
  if pid="$(pid_from_file "${file}" 2>/dev/null)" && pid_alive "${pid}"; then
    log "stopping ${label} pid=${pid}"
    kill -TERM -- "-${pid}" >/dev/null 2>&1 || true
    kill -TERM "${pid}" >/dev/null 2>&1 || true
    local i
    for ((i = 1; i <= 20; i++)); do
      pid_alive "${pid}" || break
      sleep 1
    done
    if pid_alive "${pid}"; then
      warn "${label} did not stop after SIGTERM; sending SIGKILL"
      kill -KILL -- "-${pid}" >/dev/null 2>&1 || true
      kill -KILL "${pid}" >/dev/null 2>&1 || true
    fi
  else
    log "${label}: no managed process"
  fi
  rm -f "${file}"
}

kill_port_processes() {
  local label="$1"
  local port="$2"
  local pids
  pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
  if [[ -z "${pids}" ]] && command -v fuser >/dev/null 2>&1; then
    pids="$(fuser -n tcp "${port}" 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
  fi
  if [[ -n "${pids}" ]]; then
    warn "stopping unmanaged ${label} listener(s) on ${port}: ${pids}"
    # shellcheck disable=SC2086
    kill -TERM ${pids} >/dev/null 2>&1 || true
    sleep 2
    pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
    if [[ -z "${pids}" ]] && command -v fuser >/dev/null 2>&1; then
      pids="$(fuser -n tcp "${port}" 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
    fi
    if [[ -n "${pids}" ]]; then
      # shellcheck disable=SC2086
      kill -KILL ${pids} >/dev/null 2>&1 || true
    fi
  fi
}

record_listener_pid() {
  local label="$1"
  local port="$2"
  local file="$3"
  local pid
  pid="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [[ -z "${pid}" ]] && command -v fuser >/dev/null 2>&1; then
    pid="$(fuser -n tcp "${port}" 2>/dev/null | tr ' ' '\n' | sed '/^$/d' | head -n 1 || true)"
  fi
  if [[ -n "${pid}" ]]; then
    printf '%s\n' "${pid}" > "${file}"
    log "${label}: recorded listener pid=${pid}"
  fi
}

ensure_herdmaster_token() {
  if [[ ! -f "${HERDMASTER_TOKEN_FILE}" ]]; then
    umask 077
    if command -v openssl >/dev/null 2>&1; then
      openssl rand -hex 24 > "${HERDMASTER_TOKEN_FILE}"
    else
      date +%s%N | sha256sum | awk '{print $1}' > "${HERDMASTER_TOKEN_FILE}"
    fi
  fi
  chmod 600 "${HERDMASTER_TOKEN_FILE}" 2>/dev/null || true
}

herdmaster_token() {
  ensure_herdmaster_token
  tr -d '\r\n' < "${HERDMASTER_TOKEN_FILE}"
}

write_herdmaster_config() {
  ensure_herdmaster_token
  local token
  local tmp_config
  token="$(herdmaster_token)"
  tmp_config="$(mktemp "${HERDMASTER_CONFIG}.tmp.XXXXXX")"
  chmod 600 "${tmp_config}" 2>/dev/null || true
  cat > "${tmp_config}" <<EOF
[paths]
config_dir = "${RUNTIME_DIR}/herdmaster"
db = "herdmaster.db"
socket = "herdmaster.sock"
log = "herdmaster.log"

[watchdog]
soft_timeout_s = 10.0
hard_timeout_s = 30.0
poll_interval_s = 15
max_retries = 3
tertiary_hash_interval_s = 30

[bus]
socket_path = "${RUNTIME_DIR}/herdmaster/herdmaster.sock"
message_ttl_s = 300

[acl]
default_policy = "deny"

[[acl.roles]]
name = "orchestrator"
agents = ["cli"]
can_send_to = ["*"]
can_receive_from = ["*"]
can_dispatch_tasks = true
can_reassign_tasks = true

[[acl.roles]]
name = "worker"
agents = ["*"]
can_send_to = ["cli"]
can_receive_from = ["cli"]
can_dispatch_tasks = false
can_reassign_tasks = false

[api]
bind = "127.0.0.1"
port = 8080
token = "${token}"

[database]
url = "${DATABASE_URL}"

[logging]
level = "INFO"
json = true
EOF
  mv "${tmp_config}" "${HERDMASTER_CONFIG}"
  chmod 600 "${HERDMASTER_CONFIG}" 2>/dev/null || true
}

herdmaster_auth_header() {
  printf 'Authorization: Bearer %s' "$(herdmaster_token)"
}

uvicorn_bin() {
  if [[ -x "/tmp/aop-control-plane-venv/bin/uvicorn" ]]; then
    printf '%s\n' "/tmp/aop-control-plane-venv/bin/uvicorn"
  elif command -v uvicorn >/dev/null 2>&1; then
    command -v uvicorn
  else
    die "uvicorn not found; install AOP control-plane dependencies first"
  fi
}

print_status_table() {
  local obs_mode
  obs_mode="$(observability_network_mode)"
  printf '\n%-24s %-10s %s\n' "Component" "Status" "URL"
  printf '%-24s %-10s %s\n' "---------" "------" "---"
  printf '%-24s %-10s %s\n' "Postgres" "$(port_listening 5432 && echo up || echo down)" "127.0.0.1:5432"
  printf '%-24s %-10s %s\n' "Redis" "$(port_listening 6379 && echo up || echo down)" "127.0.0.1:6379"
  printf '%-24s %-10s %s\n' "Prometheus" "$(http_code http://127.0.0.1:9090/-/healthy)" "http://127.0.0.1:9090 (${obs_mode})"
  printf '%-24s %-10s %s\n' "Grafana" "$(http_code http://127.0.0.1:3000/api/health)" "http://127.0.0.1:3000 (${obs_mode})"
  printf '%-24s %-10s %s\n' "Alertmanager" "$(http_code http://127.0.0.1:9093/-/ready)" "http://127.0.0.1:9093 (${obs_mode})"
  printf '%-24s %-10s %s\n' "Blackbox" "$(http_code http://127.0.0.1:9115/-/healthy)" "http://127.0.0.1:9115 (${obs_mode})"
  printf '%-24s %-10s %s\n' "Remediation Webhook" "$(http_code http://127.0.0.1:9099/health)" "http://127.0.0.1:9099/health (${obs_mode})"
  printf '%-24s %-10s %s\n' "HerdMaster" "$(http_code http://127.0.0.1:8080/metrics -H "$(herdmaster_auth_header)")" "http://127.0.0.1:8080/metrics"
  printf '%-24s %-10s %s\n' "AOP API" "$(http_code http://127.0.0.1:8090/health)" "http://127.0.0.1:8090"
  printf '%-24s %-10s %s\n' "AOP Frontend" "$(http_code http://127.0.0.1:13000)" "http://127.0.0.1:13000"
}
