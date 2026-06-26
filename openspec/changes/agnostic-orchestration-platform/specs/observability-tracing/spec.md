## ADDED Requirements

### Requirement: End-to-End Trace Across Layers
The system SHALL propagate a single `trace_id` across all layers (product → orchestration
brain → control plane → execution/session) so a single agent run can be followed from its
issue down to the terminal session and back.

#### Scenario: Follow a run end-to-end
- **WHEN** an operator opens a run by `trace_id`
- **THEN** they see the linked issue, plan/DAG node, dispatch, session/PTY, cost, and transcript

### Requirement: Per-Agent And Per-Runtime Traceability
The system SHALL provide full traceability scoped to an individual agent OR runtime, so an
operator can isolate the complete activity of a single agent/runtime (chain-of-thought,
tool calls, state transitions, token/seat burn, errors) independently of other agents.

#### Scenario: Trace a single agent
- **WHEN** an operator selects one agent
- **THEN** the system shows that agent's full timeline — reasoning, tool calls, state changes, and cost — filtered to that agent only

#### Scenario: Trace a single runtime
- **WHEN** an operator selects one runtime (e.g., a specific Codex seat/process)
- **THEN** the system shows all tasks/agents that ran on that runtime with their traces, linked by `trace_id`

#### Scenario: Per-agent burn isolation
- **WHEN** viewing a single agent
- **THEN** its real-time token/seat burn-rate is shown individually, not only as a squad aggregate

### Requirement: Metrics, Logs, And Alerts
The platform SHALL reuse the HerdMaster observability stack (Prometheus, Grafana,
Alertmanager, Blackbox) and expose structured logs and metrics for agents, seats, queue,
and quota.

#### Scenario: Quota burn alert fires
- **WHEN** burn-rate forecasting predicts cap exhaustion
- **THEN** an Alertmanager alert fires and is visible on the Grafana dashboard

### Requirement: Session Recording For Deep-Dive
The system SHALL persist a queryable session recording (PTY transcript) per run as a
first-class troubleshooting artifact.

#### Scenario: Troubleshoot a failed run
- **WHEN** a run fails and an operator opens its record
- **THEN** the full PTY transcript is available for replay/inspection, linked by `trace_id`

### Requirement: Audit Log
The system SHALL record all security-relevant actions (seat lease, topology violation,
autonomy decisions, billing events) in an immutable audit log.

#### Scenario: Topology violation audited
- **WHEN** a disallowed inter-agent message is blocked
- **THEN** an audit entry records source, target, action, and `trace_id`
