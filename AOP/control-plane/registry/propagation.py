"""Propagation hooks for consumers derived from the agent registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .models import AgentRecord


@dataclass(frozen=True, slots=True)
class PropagationEvent:
    """A one-action registry mutation that downstream consumers must derive from."""

    action: str
    agent: AgentRecord
    reason: str = ""


class PropagationHook(Protocol):
    """Interface implemented by ACL, allowlist, observability, and scheduler hooks."""

    name: str

    def propagate(self, event: PropagationEvent) -> None:
        """Apply a registry mutation to one downstream consumer."""


@dataclass(slots=True)
class RecordingPropagationHook:
    """In-memory hook useful as a safe stub and for tests."""

    name: str
    events: list[PropagationEvent] = field(default_factory=list)

    def propagate(self, event: PropagationEvent) -> None:
        self.events.append(event)


class AclPropagationHook(RecordingPropagationHook):
    """Stub ACL propagation hook wired through the common propagation API."""

    def __init__(self) -> None:
        super().__init__("acl")


class AllowlistPropagationHook(RecordingPropagationHook):
    """Stub allowlist propagation hook wired through the common propagation API."""

    def __init__(self) -> None:
        super().__init__("allowlist")


class ObservabilityPropagationHook(RecordingPropagationHook):
    """Stub observability target propagation hook wired through the common API."""

    def __init__(self) -> None:
        super().__init__("observability")


class SchedulerPropagationHook(RecordingPropagationHook):
    """Stub scheduler propagation hook wired through the common propagation API."""

    def __init__(self) -> None:
        super().__init__("scheduler")


@dataclass(slots=True)
class CompositePropagationHook:
    """Fan out each registry mutation to all registered hooks."""

    hooks: tuple[PropagationHook, ...]
    name: str = "composite"

    @classmethod
    def default(cls) -> "CompositePropagationHook":
        """Return the default propagation set required by the registry capability."""
        return cls(
            (
                AclPropagationHook(),
                AllowlistPropagationHook(),
                ObservabilityPropagationHook(),
                SchedulerPropagationHook(),
            )
        )

    def propagate(self, event: PropagationEvent) -> None:
        for hook in self.hooks:
            hook.propagate(event)
