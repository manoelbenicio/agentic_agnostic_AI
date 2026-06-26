## ADDED Requirements

### Requirement: Tech-Lead Coordinator As A Seat
The system SHALL support designating an agent seat as the **Tech-Lead** (coordinator) for a
task or squad. The Tech-Lead decomposes the objective and dispatches work to worker agents.
No separate LLM-API call is required; the Tech-Lead is itself an agent seat. The Tech-Lead
MUST be selectable per squad on the canvas and MUST NOT be hardcoded to any specific agent.

#### Scenario: Customer selects the Tech-Lead per squad
- **WHEN** a customer builds a squad and designates any agent seat as Tech-Lead on the canvas
- **THEN** that seat becomes the coordinator for the squad, with no hardcoded default agent

#### Scenario: Tech-Lead decomposes an objective
- **WHEN** a goal is assigned to a squad with a designated Tech-Lead
- **THEN** the Tech-Lead produces a plan and dispatches subtasks to permitted worker agents

### Requirement: Bounded Fan-Out
The Tech-Lead SHALL be able to spawn subagents (target average 2–3 per agent) subject to
admission control. Subagents inherit the parent's seat and are short-lived.

#### Scenario: Fan-out within limits
- **WHEN** the Tech-Lead requests 3 subagents and admission control permits
- **THEN** 3 short-lived subagents are spawned under the parent seat and terminate on completion

#### Scenario: Fan-out throttled by admission control
- **WHEN** the requested fan-out would exceed the concurrency/quota ceiling
- **THEN** excess subagents are queued until capacity is available

### Requirement: Configurable Autonomy Level
The Tech-Lead's authority SHALL be governed by a configurable autonomy level (e.g., 0–4)
controlling whether it may spend budget or spawn agents without human approval.

#### Scenario: Low autonomy requires approval
- **WHEN** autonomy level requires human approval and the Tech-Lead proposes a plan
- **THEN** execution pauses for human approval before any spend or spawn

#### Scenario: High autonomy proceeds
- **WHEN** autonomy level permits autonomous operation within budget
- **THEN** the Tech-Lead dispatches without per-step human approval, still bounded by budget and topology
