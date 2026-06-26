# AOP Smoke E2E Report

- Run ID: `e2e-20260626T044259Z`
- Base URL: `http://127.0.0.1:8090`
- Generated UTC: `2026-06-26T04:42:59.797302+00:00`

## Result

- Overall: `passed`
- Health: `passed`
- Ready: `passed`
- Metrics: `passed`
- Topology ACL default-deny lateral block: `passed`
- Socket task lifecycle: `passed`
- Terminal task lifecycle: `passed`
- Trace filters: `passed`
- FinOps rollup: `passed`
- WebSocket trace: `passed`

## Evidence File

- `evidence.json`

## Gaps / Backlog

- AOP has no public send_message/handoff endpoint yet; lateral block was proven by applying HerdMaster AclEngine to the effective ACL returned by /squads/{id}/topology.
- HerdMaster :8080 returned 401 without bearer token in this environment, so socket-mode dispatch used the ADR-001 fallback path unless a tokenized HerdMaster client is added.
- GET /health does not expose coupling_status yet; AppState has it, but the route response omits it.
