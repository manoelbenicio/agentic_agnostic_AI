"""Dependency wiring for the integrated control-plane app."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import redis

from coupling import CouplingStatus, build_coupled_executors
from core import (
    AdapterMetering,
    AgentState,
    OperationMode,
    RuntimeRef,
    TaskEnvelope,
)
from executors import SocketExecutor, TerminalExecutor, build_mode_router
from finops import FinOpsEngine, FinOpsRepository
from finops.schema import connect as connect_finops
from finops.schema import init_schema as init_finops_schema
from registry import AgentRegistryRepository, AgentRegistryService, CompositePropagationHook
from registry.schema import connect as connect_registry
from registry.schema import init_schema as init_registry_schema
from scheduler import QuotaAwareScheduler, QuotaLedger
from seats.pool import Seat, SeatPool
from topology.mapper import CanvasEdge, CanvasNode, TopologyMapper
from topology.repository import TopologyRepository
from tracing import TraceRepository, TraceService
from tracing.schema import connect as connect_tracing
from tracing.schema import init_schema as init_tracing_schema

from .settings import Settings


class InMemoryQueueClient:
    """Local socket queue stub used until HerdMaster HTTP wiring is enabled."""

    def __init__(self) -> None:
        self.tasks: dict[str, dict[str, Any]] = {}

    async def enqueue(self, task: TaskEnvelope) -> Mapping[str, Any]:
        self.tasks[task.task_id] = {"state": "queued", "task_id": task.task_id}
        return self.tasks[task.task_id]

    async def claim(self, task: TaskEnvelope) -> Mapping[str, Any]:
        self.tasks.setdefault(task.task_id, {"task_id": task.task_id})["state"] = "claimed"
        return self.tasks[task.task_id]

    async def mark_running(self, task: TaskEnvelope) -> Mapping[str, Any]:
        self.tasks.setdefault(task.task_id, {"task_id": task.task_id})["state"] = "running"
        return self.tasks[task.task_id]

    async def poll(self, task: TaskEnvelope) -> Mapping[str, Any]:
        self.tasks.setdefault(task.task_id, {"task_id": task.task_id})["state"] = "done"
        return self.tasks[task.task_id]


class LocalRuntimeAdapter:
    """Terminal runtime stub that exercises the terminal executor contract."""

    async def spawn(self, task: TaskEnvelope) -> RuntimeRef:
        return RuntimeRef(
            runtime_id=task.assignee_runtime,
            vendor=task.assignee_runtime,
            mode=OperationMode.TERMINAL,
            native_ref=task.assignee_runtime,
        )

    async def send(self, runtime: RuntimeRef, payload: str) -> None:
        return None

    async def read_state(self, runtime: RuntimeRef) -> AgentState:
        return AgentState.DONE

    async def stop(self, runtime: RuntimeRef) -> None:
        return None

    async def restore(self, runtime: RuntimeRef) -> RuntimeRef:
        return runtime

    async def meter(
        self,
        runtime: RuntimeRef,
        usage_hint: Mapping[str, Any] | None = None,
    ) -> AdapterMetering:
        return AdapterMetering(
            runtime_id=runtime.runtime_id,
            usage_units={"seat_seconds": Decimal(str((usage_hint or {}).get("seat_seconds", 0)))},
        )


@dataclass(slots=True)
class AppState:
    """Stateful dependency container for the integrated API."""

    settings: Settings
    registry_repo: AgentRegistryRepository
    registry_service: AgentRegistryService
    finops_repo: FinOpsRepository
    finops_engine: FinOpsEngine
    trace_repo: TraceRepository
    trace_service: TraceService
    topology_repo: TopologyRepository
    seat_pool: SeatPool
    scheduler: QuotaAwareScheduler
    mode_router: Any
    coupling_status: CouplingStatus
    redis_client: redis.Redis
    postgres_connections: list[Any] = field(default_factory=list)

    def close(self) -> None:
        for conn in self.postgres_connections:
            conn.close()
        self.redis_client.close()


def build_state(settings: Settings | None = None) -> AppState:
    """Build and initialize all control-plane module dependencies."""
    settings = settings or Settings.from_env()

    registry_conn = connect_registry(database_url=settings.database_url)
    init_registry_schema(registry_conn)
    finops_conn = connect_finops(database_url=settings.database_url)
    init_finops_schema(finops_conn)
    tracing_conn = connect_tracing(database_url=settings.database_url)
    init_tracing_schema(tracing_conn)

    registry_repo = AgentRegistryRepository(registry_conn)
    registry_service = AgentRegistryService(
        repository=registry_repo,
        propagation=CompositePropagationHook.default(),
        enrolled_workspaces={"default", "workspace-main"},
    )
    finops_repo = FinOpsRepository(finops_conn)
    trace_repo = TraceRepository(tracing_conn)

    seat_pool = SeatPool()
    seat_pool.register_seat(Seat("local-seat-codex", "tenant-a", "codex", "/tmp/aop-seat-codex"))

    coupled = build_coupled_executors(
        fallback_terminal_adapter=LocalRuntimeAdapter(),
        fallback_queue_client=InMemoryQueueClient(),
        herdmaster_url=os.environ.get("HERDMASTER_URL", "http://127.0.0.1:8080"),
        herdmaster_token=os.environ.get("HERDMASTER_TOKEN") or None,
        herdr_socket_path=os.environ.get("HERDR_SOCKET_PATH"),
    )

    return AppState(
        settings=settings,
        registry_repo=registry_repo,
        registry_service=registry_service,
        finops_repo=finops_repo,
        finops_engine=FinOpsEngine(finops_repo),
        trace_repo=trace_repo,
        trace_service=TraceService(trace_repo),
        topology_repo=TopologyRepository(settings.database_url),
        seat_pool=seat_pool,
        scheduler=QuotaAwareScheduler(QuotaLedger()),
        mode_router=build_mode_router(coupled.terminal, coupled.socket),
        coupling_status=coupled.status,
        redis_client=redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1),
        postgres_connections=[registry_conn, finops_conn, tracing_conn],
    )


async def collect_events(task: TaskEnvelope, state: AppState) -> list[dict[str, Any]]:
    """Dispatch through ModeRouter and serialize lifecycle events."""
    executor = state.mode_router.route(task)
    events: list[dict[str, Any]] = []
    async for event in executor.dispatch(task):
        events.append(event.model_dump(mode="json"))
    return events


def map_topology(nodes: list[dict[str, str]], edges: list[dict[str, str]]) -> Any:
    """Convert canvas JSON into HerdMaster ACL config using topology mapper."""
    canvas_nodes, canvas_edges = canvas_topology(nodes, edges)
    return TopologyMapper.map_to_acl(canvas_nodes, canvas_edges)


def canvas_topology(
    nodes: list[dict[str, str]],
    edges: list[dict[str, str]],
) -> tuple[list[CanvasNode], list[CanvasEdge]]:
    """Convert canvas JSON into topology dataclasses."""
    canvas_nodes = [CanvasNode(id=item["id"], role=item["role"]) for item in nodes]
    canvas_edges = [CanvasEdge(source=item["source"], target=item["target"]) for item in edges]
    return canvas_nodes, canvas_edges


async def close_state(state: AppState) -> None:
    await asyncio.to_thread(state.close)
