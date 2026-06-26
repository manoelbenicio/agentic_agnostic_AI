## ADDED Requirements

### Requirement: Isolated Maximum Parallelism
The system SHALL support running many agents in parallel at maximum concurrency while
guaranteeing that one agent's work cannot overwrite or break another agent's code. Isolation
MUST be enforced via independent workspaces (e.g., Git worktrees) and/or path guards.

#### Scenario: Two agents edit in parallel safely
- **WHEN** two agents work concurrently on different tasks
- **THEN** each operates in an isolated workspace/path scope and neither can modify the other's files

#### Scenario: Path-guard blocks out-of-scope write
- **WHEN** an agent attempts to write outside its allowed path scope
- **THEN** the write is blocked and the violation is recorded

### Requirement: On-Disk Check-In/Check-Out Ledger
The system SHALL write a check-in/check-out control file to disk in the project folder. Every
agent MUST record a CHECK-IN when starting an activity and a CHECK-OUT when finishing, each with
a UTC timestamp and the agent name. Entries are append-only and never overwrite prior lines.

#### Scenario: Agent checks in on start
- **WHEN** an agent begins a task
- **THEN** a CHECK-IN line with UTC timestamp, agent name, task id, and files it will touch is appended to the on-disk ledger

#### Scenario: Agent checks out on finish
- **WHEN** an agent finishes (or fails) a task
- **THEN** a CHECK-OUT line with UTC timestamp, agent name, task id, exact files touched, and status is appended

#### Scenario: Missing check-out flagged
- **WHEN** a task has a CHECK-IN but no CHECK-OUT after its timeout
- **THEN** the system flags it as a protocol violation

### Requirement: Mandatory Evidence On Task Delivery
Every task delivery SHALL include verifiable evidence (e.g., screenshot, output file path, SHA-256
hash of delivered files, or a link to generated output). A CHECK-OUT without evidence MUST be
treated as invalid.

#### Scenario: Delivery with evidence accepted
- **WHEN** an agent completes a task and attaches evidence (screenshot/file/hash)
- **THEN** the delivery is accepted and the evidence is linked to the task and its `trace_id`

#### Scenario: Delivery without evidence rejected
- **WHEN** an agent marks a task done with no evidence
- **THEN** the system rejects the completion as invalid and keeps the task open
