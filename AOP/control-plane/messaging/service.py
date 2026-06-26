"""Runtime messaging with live topology ACL enforcement."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from herdmaster.acl.engine import AclDenied, AclEngine
from herdmaster.bus.messages import Message, MessageType, new_message
from topology.mapper import CanvasEdge, CanvasNode, TopologyMapper

from tracing import TraceLayer, TraceSignalType


MessageOperation = Literal["send_message", "handoff"]


class RuntimeMessageRequest(BaseModel):
    """HTTP body for runtime agent-to-agent messaging."""

    operation: MessageOperation = "send_message"
    from_agent: str = Field(min_length=1)
    to_agent: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    content: str | None = None
    trace_id: str | None = None
    tenant_id: str = "tenant-a"
    project_id: str = "project-a"
    issue_id: str = "issue-default"
    runtime_id: str | None = None
    ttl_seconds: int = Field(default=300, ge=0)


class TopologyViolation(Exception):
    """Raised when a runtime message violates effective squad topology."""

    def __init__(
        self,
        *,
        trace_id: str,
        from_agent: str,
        to_agent: str,
        reason: str,
        roles_checked: list[str],
        audit_event_id: str | None,
    ) -> None:
        self.trace_id = trace_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.reason = reason
        self.roles_checked = roles_checked
        self.audit_event_id = audit_event_id
        super().__init__(reason)


@dataclass(slots=True)
class InMemoryMessageBus:
    """Fallback route used when a HerdMaster MessageBus is not wired."""

    sent: list[Message] = field(default_factory=list)

    async def send(self, message: Message) -> None:
        self.sent.append(message)


_fallback_bus = InMemoryMessageBus()


async def route_runtime_message(
    *,
    squad_id: str,
    request: RuntimeMessageRequest,
    state: Any,
) -> dict[str, Any]:
    """Validate topology, audit the attempt, and route a runtime message."""

    trace_id = request.trace_id or state.trace_service.new_trace_id()
    message = _message_from_request(request, trace_id)
    acl_engine = _acl_engine_for_squad(state.topology_repo, squad_id)

    try:
        acl_engine.check_message(message)
    except AclDenied as exc:
        audit_event = _audit(
            state,
            request=request,
            trace_id=trace_id,
            allowed=False,
            message_id=message.id,
            reason=exc.reason,
            roles_checked=exc.roles_checked,
        )
        raise TopologyViolation(
            trace_id=trace_id,
            from_agent=exc.from_agent,
            to_agent=exc.to_agent,
            reason=exc.reason,
            roles_checked=exc.roles_checked,
            audit_event_id=getattr(audit_event, "event_id", None),
        ) from exc

    route = await _send_via_available_bus(state, message)
    audit_event = _audit(
        state,
        request=request,
        trace_id=trace_id,
        allowed=True,
        message_id=message.id,
        reason="allowed by effective topology",
        roles_checked=[],
    )
    return {
        "ok": True,
        "squad_id": squad_id,
        "trace_id": trace_id,
        "message_id": message.id,
        "operation": request.operation,
        "from_agent": message.from_agent,
        "to_agent": message.to,
        "route": route,
        "audit_event_id": getattr(audit_event, "event_id", None),
    }


def _acl_engine_for_squad(topology_repo: Any, squad_id: str) -> AclEngine:
    stored = topology_repo.get_topology(squad_id)
    if not stored:
        return AclEngine(TopologyMapper.map_to_acl([], []))

    nodes = stored.get("nodes") or []
    edges = stored.get("edges") or []
    canvas_nodes = [CanvasNode(id=item["id"], role=item["role"]) for item in nodes]
    canvas_edges = [CanvasEdge(source=item["source"], target=item["target"]) for item in edges]
    return AclEngine(TopologyMapper.map_to_acl(canvas_nodes, canvas_edges))


def _message_from_request(request: RuntimeMessageRequest, trace_id: str) -> Message:
    payload = dict(request.payload)
    if request.content is not None:
        payload["content"] = request.content
    payload["operation"] = request.operation
    payload["trace_id"] = trace_id
    return new_message(
        MessageType.CHAT,
        from_agent=request.from_agent,
        to=request.to_agent,
        payload=payload,
        correlation_id=trace_id,
        ttl_seconds=request.ttl_seconds,
    )


async def _send_via_available_bus(state: Any, message: Message) -> str:
    bus = getattr(state, "message_bus", None) or getattr(state, "bus", None)
    if bus is None:
        bus = _fallback_bus
        route = "fallback"
    else:
        route = "herdmaster_message_bus"

    result = bus.send(message)
    if inspect.isawaitable(result):
        await result
    return route


def _audit(
    state: Any,
    *,
    request: RuntimeMessageRequest,
    trace_id: str,
    allowed: bool,
    message_id: str,
    reason: str,
    roles_checked: list[str],
) -> Any:
    return state.trace_service.record(
        trace_id=trace_id,
        layer=TraceLayer.L2_CONTROL_PLANE,
        signal_type=TraceSignalType.AUDIT,
        tenant_id=request.tenant_id,
        project_id=request.project_id,
        issue_id=request.issue_id,
        agent_id=request.from_agent,
        runtime_id=request.runtime_id or request.from_agent,
        message="runtime message allowed" if allowed else "topology_violation",
        details={
            "allowed": allowed,
            "reason": reason,
            "message_id": message_id,
            "operation": request.operation,
            "from_agent": request.from_agent,
            "to_agent": request.to_agent,
            "roles_checked": roles_checked,
        },
    )
