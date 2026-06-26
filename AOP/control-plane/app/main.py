"""FastAPI app integrating AOP control-plane modules."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any

import psycopg
import redis
from fastapi import Depends, FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core import OperationMode, TaskBudget, TaskEnvelope
from finops import Attribution, SeatUsage, TokenUsage
from messaging import RuntimeMessageRequest, TopologyViolation, route_runtime_message
from registry import PaneRef
from tracing import TraceLayer, TraceSignalType

from .dependencies import AppState, build_state, canvas_topology, close_state, collect_events, map_topology
from .schemas import (
    AgentCreateRequest,
    SeatCostRequest,
    TaskCreateRequest,
    TokenCostRequest,
    TopologySaveRequest,
    TraceArtifactRequest,
    TraceEventRequest,
)
from .settings import Settings


def create_app(settings: Settings | None = None, state: AppState | None = None) -> FastAPI:
    """Create the integrated FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = state or build_state(settings)
        try:
            yield
        finally:
            await close_state(app.state.container)

    effective_settings = settings or Settings.from_env()
    app = FastAPI(title="Agnostic Orchestration Platform Control Plane", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(effective_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def container() -> AppState:
        return app.state.container

    @app.get("/health")
    def health(state: AppState = Depends(container)) -> dict[str, Any]:
        return {"status": "ok", "coupling": _coupling_health(state)}

    @app.get("/health/ready")
    def ready(state: AppState = Depends(container)) -> dict[str, Any]:
        checks: dict[str, bool] = {"postgres": False, "redis": False}
        try:
            with state.postgres_connections[0].cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                checks["postgres"] = bool(cur.fetchone()["ok"])
        except psycopg.Error:
            checks["postgres"] = False
        try:
            checks["redis"] = bool(state.redis_client.ping())
        except redis.RedisError:
            checks["redis"] = False
        if not all(checks.values()):
            raise HTTPException(status_code=503, detail=checks)
        return {"status": "ready", "checks": checks, "coupling": _coupling_health(state)}

    @app.post("/tasks")
    async def create_task(
        request: TaskCreateRequest,
        state: AppState = Depends(container),
    ) -> dict[str, Any]:
        task = TaskEnvelope(
            task_id=request.task_id,
            tenant_id=request.tenant_id,
            project_id=request.project_id,
            assignee_runtime=request.assignee_runtime,
            prompt=request.prompt,
            credential_ref=request.credential_ref,
            operation_mode=OperationMode(request.operation_mode),
            budget=TaskBudget(seat_seconds=request.seat_seconds or None),
        )
        events = await collect_events(task, state)
        return {"task_id": task.task_id, "operation_mode": task.operation_mode.value, "events": events}

    @app.post("/squads/{squad_id}/topology")
    def save_topology(
        squad_id: str,
        request: TopologySaveRequest,
        state: AppState = Depends(container),
    ) -> dict[str, Any]:
        acl = map_topology(request.nodes, request.edges)
        nodes, edges = canvas_topology(request.nodes, request.edges)
        state.topology_repo.save_topology(squad_id, nodes, edges)
        return {
            "squad_id": squad_id,
            "effective_topology": {
                "default_policy": acl.default_policy,
                "roles": [_acl_role(role) for role in acl.roles],
            },
        }

    @app.get("/squads/{squad_id}/topology")
    def get_topology(squad_id: str, state: AppState = Depends(container)) -> dict[str, Any]:
        stored = state.topology_repo.get_topology(squad_id)
        return {"squad_id": squad_id, "stored": stored}

    @app.post("/squads/{squad_id}/messages")
    async def send_message(
        squad_id: str,
        request: RuntimeMessageRequest,
        state: AppState = Depends(container),
    ) -> dict[str, Any]:
        try:
            return await route_runtime_message(squad_id=squad_id, request=request, state=state)
        except TopologyViolation as exc:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "topology_violation",
                    "trace_id": exc.trace_id,
                    "from_agent": exc.from_agent,
                    "to_agent": exc.to_agent,
                    "reason": exc.reason,
                    "roles_checked": exc.roles_checked,
                    "audit_event_id": exc.audit_event_id,
                },
            ) from exc

    @app.post("/agents")
    def create_agent(
        request: AgentCreateRequest,
        state: AppState = Depends(container),
    ) -> dict[str, Any]:
        pane = (
            PaneRef(workspace_id=request.workspace_id, pane_id=request.pane_id)
            if request.workspace_id and request.pane_id
            else None
        )
        agent = state.registry_service.add_agent(
            tenant_id=request.tenant_id,
            label=request.label,
            vendor=request.vendor,
            role=request.role,
            pane=pane,
            stable_key=request.stable_key,
            metadata=request.metadata,
        )
        return _agent(agent)

    @app.get("/agents")
    def list_agents(state: AppState = Depends(container)) -> list[dict[str, Any]]:
        return [_agent(agent) for agent in state.registry_repo.list_agents()]

    @app.delete("/agents/{agent_id}")
    def delete_agent(agent_id: str, state: AppState = Depends(container)) -> dict[str, Any]:
        agent = state.registry_service.remove_agent(agent_id, reason="api delete")
        if agent is None:
            raise HTTPException(status_code=404, detail="agent not found")
        return _agent(agent)

    @app.get("/seats")
    def seats(state: AppState = Depends(container)) -> dict[str, Any]:
        return {
            "seats": [
                {
                    "seat_id": seat.seat_id,
                    "tenant_id": seat.tenant_id,
                    "vendor": seat.vendor,
                    "leased": seat.ref_count > 0,
                    "ref_count": seat.ref_count,
                }
                for seat in state.seat_pool.all_seats.values()
            ]
        }

    @app.post("/finops/costs/token")
    def record_token_cost(request: TokenCostRequest, state: AppState = Depends(container)) -> dict[str, Any]:
        record = state.finops_engine.record_token_usage(
            _attribution(request),
            TokenUsage(
                input_tokens=request.input_tokens,
                output_tokens=request.output_tokens,
                input_token_price_usd=request.input_token_price_usd,
                output_token_price_usd=request.output_token_price_usd,
                model=request.model,
            ),
            trace_id=request.trace_id,
        )
        return _cost(record)

    @app.post("/finops/costs/seat")
    def record_seat_cost(request: SeatCostRequest, state: AppState = Depends(container)) -> dict[str, Any]:
        record = state.finops_engine.record_seat_usage(
            _attribution(request),
            SeatUsage(
                seat_id=request.seat_id,
                vendor=request.vendor,
                used_seconds=request.used_seconds,
                period_seconds=request.period_seconds,
                period_cost_usd=request.period_cost_usd,
            ),
            trace_id=request.trace_id,
        )
        return _cost(record)

    @app.get("/finops/projects/{tenant_id}/{project_id}/rollup")
    def project_rollup(tenant_id: str, project_id: str, state: AppState = Depends(container)) -> dict[str, Any]:
        rollup = state.finops_repo.rollup_project(tenant_id, project_id)
        return {
            "tenant_id": rollup.tenant_id,
            "project_id": rollup.project_id,
            "total_cost_usd": str(rollup.total_cost_usd),
            "token_cost_usd": str(rollup.token_cost_usd),
            "seat_cost_usd": str(rollup.seat_cost_usd),
            "record_count": rollup.record_count,
        }

    @app.post("/tracing/events")
    def record_trace(request: TraceEventRequest, state: AppState = Depends(container)) -> dict[str, Any]:
        event = state.trace_service.record(
            trace_id=request.trace_id,
            layer=TraceLayer(request.layer),
            signal_type=TraceSignalType(request.signal_type),
            tenant_id=request.tenant_id,
            project_id=request.project_id,
            issue_id=request.issue_id,
            agent_id=request.agent_id,
            runtime_id=request.runtime_id,
            message=request.message,
            token_burn=request.token_burn,
            seat_seconds=request.seat_seconds,
            details=request.details,
        )
        return _trace_event(event)

    @app.post("/tracing/artifacts")
    def record_artifact(request: TraceArtifactRequest, state: AppState = Depends(container)) -> dict[str, Any]:
        artifact = state.trace_service.record_session_artifact(**request.model_dump())
        return {
            "trace_id": artifact.trace_id,
            "artifact_uri": artifact.artifact_uri,
            "runtime_id": artifact.runtime_id,
            "agent_id": artifact.agent_id,
        }

    @app.get("/tracing/agents/{agent_id}")
    def trace_agent(agent_id: str, state: AppState = Depends(container)) -> list[dict[str, Any]]:
        return [_trace_event(event) for event in state.trace_service.timeline_for_agent(agent_id)]

    @app.websocket("/ws/tracing/agents/{agent_id}")
    async def trace_agent_ws(websocket: WebSocket, agent_id: str) -> None:
        await websocket.accept()
        state: AppState = container()
        seen_event_ids: set[str] = set()

        async def send_new_events() -> None:
            events = [
                _trace_event(event)
                for event in state.trace_service.timeline_for_agent(agent_id)
                if event.event_id not in seen_event_ids
            ]
            if events:
                seen_event_ids.update(event["event_id"] for event in events)
                await websocket.send_json(events)

        try:
            await send_new_events()
            while True:
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                except TimeoutError:
                    pass
                await send_new_events()
        except WebSocketDisconnect:
            return

    @app.get("/tracing/runtimes/{runtime_id}")
    def trace_runtime(runtime_id: str, state: AppState = Depends(container)) -> list[dict[str, Any]]:
        return [_trace_event(event) for event in state.trace_service.timeline_for_runtime(runtime_id)]

    @app.get("/metrics")
    def metrics(state: AppState = Depends(container)) -> Response:
        from finops import FinOpsMetricsExporter
        from tracing import TracingMetricsExporter

        text = [
            "# HELP aop_control_plane_up Control plane liveness",
            "# TYPE aop_control_plane_up gauge",
            "aop_control_plane_up 1",
            FinOpsMetricsExporter(state.finops_repo).project_metrics(
                tenant_id="tenant-a",
                project_id="project-a",
            ),
            TracingMetricsExporter(state.trace_repo).burn_metrics(),
        ]
        return Response("\n".join(text), media_type="text/plain")

    return app


app = create_app()


def _agent(agent: Any) -> dict[str, Any]:
    return {
        "agent_id": agent.agent_id,
        "tenant_id": agent.tenant_id,
        "label": agent.label,
        "vendor": agent.vendor,
        "role": agent.role,
        "status": agent.status.value,
        "workspace_id": agent.workspace_id,
        "pane_id": agent.pane_id,
        "stable_key": agent.stable_key,
        "metadata": agent.metadata,
    }


def _acl_role(role: Any) -> dict[str, Any]:
    return {
        "name": role.name,
        "agents": list(role.agents),
        "can_send_to": list(role.can_send_to),
        "can_receive_from": list(role.can_receive_from),
        "can_dispatch_tasks": bool(role.can_dispatch_tasks),
        "can_reassign_tasks": bool(role.can_reassign_tasks),
    }


def _attribution(request: Any) -> Attribution:
    return Attribution(
        tenant_id=request.tenant_id,
        project_id=request.project_id,
        issue_id=request.issue_id,
        agent_id=request.agent_id,
        runtime_id=request.runtime_id,
    )


def _cost(record: Any) -> dict[str, Any]:
    return {
        "cost_id": record.cost_id,
        "engine": record.engine.value,
        "billing_mode": record.billing_mode.value,
        "tenant_id": record.attribution.tenant_id,
        "project_id": record.attribution.project_id,
        "cost_usd": str(record.cost_usd),
        "usage_units": {key: str(value) for key, value in record.usage_units.items()},
        "trace_id": record.trace_id,
    }


def _trace_event(event: Any) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "trace_id": event.trace_id,
        "layer": event.layer.value,
        "signal_type": event.signal_type.value,
        "tenant_id": event.tenant_id,
        "project_id": event.project_id,
        "issue_id": event.issue_id,
        "agent_id": event.agent_id,
        "runtime_id": event.runtime_id,
        "message": event.message,
        "token_burn": event.token_burn,
        "seat_seconds": event.seat_seconds,
        "details": event.details,
    }


def _coupling_health(state: AppState) -> dict[str, str | None]:
    return {
        "status": state.coupling_status.phase.value,
        "last_error": state.coupling_status.last_error,
    }
