#!/usr/bin/env python3
"""
HerdMaster Auto-Remediation Webhook Server
==========================================
Servidor HTTP leve que recebe alertas do Alertmanager e executa
ações de auto-remediation baseadas no tipo de alerta.

Porta: 9099
Endpoints:
  POST /webhook/log        → loga o alerta (todos)
  POST /webhook/remediate  → executa purge de agentes fantasmas (auto)
  POST /webhook/critical   → loga como crítico (escalação futura)
  GET  /health             → health check

Fluxo anti-falso-positivo:
  Prometheus detecta herdmaster_unlisted_agents_total > 0
  → Alertmanager FIRING → POST /webhook/remediate
  → purge_unlisted_agents() DELETE WHERE id NOT IN whitelist
  → Prometheus scrape 5s depois → herdmaster_unlisted_agents_total = 0
  → Alertmanager RESOLVED → POST /webhook/remediate (send_resolved=true)
  → loga resolução
"""

from __future__ import annotations

import http.server
import json
import logging
import os
from datetime import datetime, UTC
from pathlib import Path

# ── Configuração ──────────────────────────────────────────────────
PORT = int(os.environ.get("WEBHOOK_PORT", "9099"))
LOG_PATH = Path(os.environ.get(
    "REMEDIATION_LOG",
    Path.home() / ".config/herdmaster/remediation.log"
))

# ── HerdMaster HTTP API client ──────────────────────────────────────────
HM_API_BASE = os.environ.get("HERDMASTER_API", "http://127.0.0.1:8080")
HM_API_TOKEN = os.environ.get("HERDMASTER_TOKEN", "admin")

# Whitelist canônica — idêntica à agent_allowlist em config.toml e engine.py
AGENT_WHITELIST: frozenset[str] = frozenset({
    "cli", "w6:p1", "w6:p2", "w6:p5", "w6:p6", "w6:p7", "w6:p8"
})

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s UTC [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("hm.remediation")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

def _log_remediation(action: str, detail: str, result: str) -> None:
    """Appends a structured line to the remediation audit log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"ts": _utc_now(), "action": action, "detail": detail, "result": result})
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    log.info("AUDIT | action=%s | %s | result=%s", action, detail, result)

# ── HerdMaster API helpers ────────────────────────────────────────────────────

def _hm_request(method: str, path: str, *, timeout: int = 10) -> dict:
    """Make an authenticated request to the HerdMaster HTTP API."""
    import urllib.request, urllib.error
    url = f"{HM_API_BASE}{path}"
    req = urllib.request.Request(
        url,
        method=method,
        headers={"Authorization": f"Bearer {HM_API_TOKEN}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {path}: {body}") from e
    except Exception as e:
        raise RuntimeError(f"Request to {path} failed: {e}") from e


def purge_unlisted_agents() -> dict:
    """
    Identifies and removes ghost agents via the HerdMaster HTTP API.

    Uses DELETE /agents/{id} for each agent not in AGENT_WHITELIST.
    This approach:
      - Avoids ALL SQLite lock contention (single DB writer = HerdMaster)
      - Is idempotent and safe to call concurrently
      - Respects HerdMaster's own transaction boundaries
    """
    try:
        # 1. Fetch current agent list from HerdMaster API
        response = _hm_request("GET", "/agents")
        agents = response.get("data", [])
        if not isinstance(agents, list):
            return {"deleted_count": 0, "deleted_ids": [], "error": "unexpected agents response format"}

        # 2. Identify unlisted agents
        unlisted = [a for a in agents if a.get("id") not in AGENT_WHITELIST]

        if not unlisted:
            return {"deleted_count": 0, "deleted_ids": []}

        # 3. Delete each unlisted agent via API (HerdMaster owns the DB write)
        deleted = []
        errors = []
        for agent in unlisted:
            agent_id = agent.get("id", "")
            try:
                _hm_request("DELETE", f"/agents/{agent_id}")
                deleted.append({"id": agent_id, "label": agent.get("label", "")})
                log.warning("PURGED ghost agent via API: %r (%s)", agent_id, agent.get("label", ""))
            except RuntimeError as e:
                errors.append(str(e))
                log.error("Failed to delete agent %r via API: %s", agent_id, e)

        result: dict = {"deleted_count": len(deleted), "deleted_ids": deleted}
        if errors:
            result["errors"] = errors
        return result

    except RuntimeError as e:
        return {"deleted_count": 0, "deleted_ids": [], "error": str(e)}


# ── Webhook Handler ───────────────────────────────────────────────────────────

class WebhookHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # suppress default access log spam
        log.debug("HTTP %s", fmt % args)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _respond(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"ok": True, "ts": _utc_now(), "api": HM_API_BASE})

        else:
            self._respond(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        body = self._read_body()
        alerts = body.get("alerts", [])
        status = body.get("status", "unknown")  # "firing" or "resolved"

        if self.path == "/webhook/log":
            self._handle_log(alerts, status)

        elif self.path == "/webhook/remediate":
            self._handle_remediate(alerts, status)

        elif self.path == "/webhook/critical":
            self._handle_critical(alerts, status)

        else:
            self._respond(404, {"ok": False, "error": "unknown webhook path"})

    def _handle_log(self, alerts: list, status: str) -> None:
        for alert in alerts:
            name = alert.get("labels", {}).get("alertname", "unknown")
            severity = alert.get("labels", {}).get("severity", "unknown")
            summary = alert.get("annotations", {}).get("summary", "")
            log.info("[%s] %s | %s | %s", status.upper(), name, severity, summary)
            _log_remediation("log", f"{name}:{status}", summary)
        self._respond(200, {"ok": True, "processed": len(alerts)})

    def _handle_remediate(self, alerts: list, status: str) -> None:
        """
        Core auto-remediation handler.
        On FIRING: executes whitelist purge.
        On RESOLVED: logs resolution only.
        """
        if status == "resolved":
            log.info("REMEDIATION RESOLVED — registry integrity restored")
            _log_remediation("resolved", "whitelist_purge", "alert resolved by Prometheus")
            self._respond(200, {"ok": True, "action": "resolved_logged"})
            return

        # FIRING → execute purge
        firing_names = [a.get("labels", {}).get("alertname", "") for a in alerts]
        log.warning("REMEDIATION TRIGGERED by: %s", firing_names)

        result = purge_unlisted_agents()

        if "error" in result:
            log.error("REMEDIATION FAILED: %s", result["error"])
            _log_remediation(
                "purge_failed",
                f"alerts={firing_names}",
                result["error"]
            )
            self._respond(500, {"ok": False, "error": result["error"]})
            return

        if result["deleted_count"] > 0:
            detail = f"deleted={[r['id'] for r in result['deleted_ids']]}"
            log.warning("REMEDIATION EXECUTED: %d agents purged | %s", result["deleted_count"], detail)
            _log_remediation("purge_executed", detail, f"deleted={result['deleted_count']}")
        else:
            log.info("REMEDIATION: no unlisted agents found (already clean)")
            _log_remediation("purge_noop", "no_unlisted_agents", "clean")

        self._respond(200, {
            "ok": True,
            "action": "purge_executed",
            "deleted_count": result["deleted_count"],
            "deleted_ids": result["deleted_ids"],
            "ts": _utc_now(),
        })

    def _handle_critical(self, alerts: list, status: str) -> None:
        for alert in alerts:
            name = alert.get("labels", {}).get("alertname", "unknown")
            summary = alert.get("annotations", {}).get("summary", "")
            log.critical("[CRITICAL/%s] %s | %s", status.upper(), name, summary)
            _log_remediation("critical", f"{name}:{status}", summary)
        # TODO: integrate Slack/PagerDuty/email here
        self._respond(200, {"ok": True, "processed": len(alerts), "escalation": "logged"})

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("HerdMaster Remediation Webhook Server starting on port %d", PORT)
    log.info("HerdMaster API: %s (token: %s)", HM_API_BASE, HM_API_TOKEN[:4] + "****")
    log.info("Whitelist (%d agents): %s", len(AGENT_WHITELIST), sorted(AGENT_WHITELIST))
    log.info("Audit log: %s", LOG_PATH)

    server = http.server.HTTPServer(("127.0.0.1", PORT), WebhookHandler)
    log.info("Listening on http://127.0.0.1:%d", PORT)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutdown requested")
        server.server_close()

if __name__ == "__main__":
    main()
