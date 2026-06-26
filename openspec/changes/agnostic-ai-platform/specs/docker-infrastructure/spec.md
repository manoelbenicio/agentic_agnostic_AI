## ADDED Requirements

### Requirement: Full Docker Compose Stack
The system SHALL define a `docker-compose.yml` in `/mnt/c/VMs/Projects/Multi_Orchestration_Project_Tasks/AgnosticAI_Platform/` with the following services: `frontend` (Next.js, port 3000), `backend` (FastAPI, port 8000), `postgres` (PostgreSQL 16, port 5432), `redis` (Redis 7, port 6379), `prometheus` (port 9090), `grafana` (port 3001), `blackbox-exporter` (port 9115). All services SHALL be on a shared internal network `agnosticai_net`.

#### Scenario: Full stack cold start
- **WHEN** `docker-compose up -d` is run on a clean environment
- **THEN** all 7 services start successfully within 60 seconds
- **THEN** `docker-compose ps` shows all services as "Up" (healthy)
- **THEN** the frontend is accessible at `http://localhost:3000`

### Requirement: Network Isolation Between Services
Services SHALL communicate only via the `agnosticai_net` bridge network. The PostgreSQL and Redis ports SHALL NOT be exposed to the host unless the environment variable `EXPOSE_DB_PORTS=true` is set. The backend is the only service with write access to the database.

#### Scenario: DB port not exposed by default
- **WHEN** `docker-compose up -d` is run without `EXPOSE_DB_PORTS=true`
- **THEN** `postgres:5432` is not accessible from the host machine
- **THEN** only the backend container can connect to postgres

### Requirement: Database Migrations via Alembic
The backend container SHALL run `alembic upgrade head` automatically on startup before accepting requests. Migration files SHALL be stored in `/AgnosticAI_Platform/src/api/migrations/`. The schema version SHALL be tracked in the `alembic_version` table in PostgreSQL.

#### Scenario: First boot migration
- **WHEN** the backend container starts against an empty PostgreSQL instance
- **THEN** all migration files are applied in order
- **THEN** the backend only starts accepting requests after migrations complete successfully

### Requirement: Environment Variable Configuration
All secrets and configuration SHALL be managed via environment variables defined in a `.env` file (gitignored). The `docker-compose.yml` SHALL reference these variables. Required variables: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `LITELLM_OPENAI_API_KEY`, `LITELLM_ANTHROPIC_API_KEY`, `LITELLM_GEMINI_API_KEY`.

#### Scenario: Missing required environment variable
- **WHEN** the backend starts without `JWT_SECRET_KEY` defined
- **THEN** the startup process fails with a clear error: "FATAL: JWT_SECRET_KEY environment variable is required"
- **THEN** the container exits with code 1 and does not accept requests
