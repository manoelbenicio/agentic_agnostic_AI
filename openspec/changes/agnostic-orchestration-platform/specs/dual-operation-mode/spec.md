## ADDED Requirements

### Requirement: Per-Task Operation Mode Selection
The system SHALL allow the user to choose, per task, whether the task executes in
**Terminal mode** (multiplexer / Herdr) or **Socket mode** (control plane + kanban).
The selected mode MUST be persisted on the task and honored by the dispatcher.

#### Scenario: User selects Terminal mode for a task
- **WHEN** a user creates or edits a task and selects `operation_mode = terminal`
- **THEN** the dispatcher routes the task to the `TerminalExecutor` (Herdr panes)
- **THEN** the task record stores `operation_mode = terminal`

#### Scenario: User selects Socket mode for a task
- **WHEN** a user creates a task and selects `operation_mode = socket`
- **THEN** the dispatcher routes the task to the `SocketExecutor` (control plane claim/poll)
- **THEN** the task surfaces on the kanban board with live status

### Requirement: Unified Task/Event Contract
Both executors SHALL consume one typed task envelope containing at minimum
`task_id, tenant_id, project_id, assignee_runtime, prompt, budget, credential_ref,
operation_mode, callbacks`. Executors MUST be interchangeable behind this contract.

#### Scenario: Same task envelope dispatched to either executor
- **WHEN** a task envelope is dispatched
- **THEN** the chosen executor consumes the identical envelope schema without transformation loss
- **THEN** lifecycle events emitted back use one common event schema regardless of mode

### Requirement: Mode-Agnostic Lifecycle Events
Regardless of operation mode, the system SHALL emit a normalized lifecycle event stream
(`queued, claimed, running, blocked, done, failed`) so that UI, FinOps, and observability
consume one event model.

#### Scenario: Terminal and Socket tasks report uniformly
- **WHEN** a Terminal-mode task and a Socket-mode task both reach completion
- **THEN** both emit a `done` event with the same field shape (timestamps, runtime, cost refs)
