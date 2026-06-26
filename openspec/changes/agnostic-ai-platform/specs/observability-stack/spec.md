## ADDED Requirements

### Requirement: Prometheus Metrics Endpoint
The backend SHALL expose a `/metrics` endpoint in Prometheus text format on port 9090. The endpoint MUST be available from the first working commit. Metrics MUST include: `agnosticai_http_requests_total{method,path,status}`, `agnosticai_http_request_duration_seconds{method,path}`, `agnosticai_llm_tokens_total{model,workspace,user}`, `agnosticai_llm_fallback_total{from_model,to_model}`, `agnosticai_active_agents{workspace}`, `agnosticai_websocket_connections{workspace}`.

#### Scenario: Prometheus scrape
- **WHEN** Prometheus scrapes `http://backend:9090/metrics`
- **THEN** all defined metrics are present in the response with correct labels
- **THEN** the scrape completes in under 500ms

### Requirement: Health Check Endpoints
The system SHALL expose `/health` (liveness) and `/health/ready` (readiness) endpoints on the backend. `/health` SHALL return HTTP 200 with `{"status": "ok"}`. `/health/ready` SHALL return HTTP 200 only when the database connection and Redis connection are healthy, HTTP 503 otherwise.

#### Scenario: Readiness probe fails on DB disconnect
- **WHEN** the PostgreSQL connection is lost
- **THEN** `GET /health/ready` returns HTTP 503 with `{"status": "unhealthy", "checks": {"db": "down", "redis": "ok"}}`
- **THEN** Prometheus alert `AgnosticAI_BackendNotReady` fires after 30s

### Requirement: Grafana Dashboards as Code
Grafana dashboards SHALL be provisioned as JSON files in `/mnt/c/VMs/Projects/Multi_Orchestration_Project_Tasks/AgnosticAI_Platform/deploy/observability/grafana/dashboards/`. At minimum, one dashboard (`agnosticai_main.json`) MUST be provisioned on first boot covering: Request Rate, Error Rate, LLM Token Consumption, Active Agents, WebSocket Connections.

#### Scenario: Stack startup provisions dashboards
- **WHEN** `docker-compose up -d` is run
- **THEN** Grafana loads all JSON files from the provisioned dashboards directory
- **THEN** the `agnosticai_main` dashboard is accessible without manual import

### Requirement: Alerting Rules
Prometheus alert rules SHALL be defined in `/deploy/observability/prometheus/alert_rules.yml`. Required alerts: `AgnosticAI_BackendNotReady` (backend readiness probe fails >30s), `AgnosticAI_HighErrorRate` (5xx rate >5% over 5m), `AgnosticAI_LLMHighLatency` (p99 latency >10s over 5m).

#### Scenario: High error rate alert
- **WHEN** the 5xx error rate exceeds 5% for 5 consecutive minutes
- **THEN** the `AgnosticAI_HighErrorRate` alert fires
- **THEN** Alertmanager routes the notification to the configured receiver
