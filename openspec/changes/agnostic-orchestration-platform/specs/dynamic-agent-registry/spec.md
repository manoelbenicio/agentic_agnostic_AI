## ADDED Requirements

### Requirement: Single Source Of Truth For Agent Identity
The platform SHALL maintain one authoritative agent registry. Agent identity and metadata
MUST NOT be duplicated across multiple hand-edited files (e.g., `config.toml` allowlist,
`webhook_server.py` whitelist, Grafana/observability config). All consumers read from the
single registry.

#### Scenario: One place to define an agent
- **WHEN** an agent is registered
- **THEN** its identity is stored once in the authoritative registry and every consumer (ACL, allowlist, observability, scheduler) derives from it without separate manual edits

### Requirement: Dynamic Add/Remove Without Manual File Edits
Adding or removing an agent (or a Herdr pane) SHALL be a single action (API/UI/canvas) that
propagates automatically. The system MUST NOT require the operator to write scripts or hand-edit
multiple files to keep allowlists, observability, and ACL in sync.

#### Scenario: Add an agent in one action
- **WHEN** an operator adds a new agent via the registry API/UI
- **THEN** the allowlist, ACL roles, observability targets, and dashboards update automatically with no manual file editing

#### Scenario: Remove a pane in one action
- **WHEN** a pane is removed
- **THEN** the agent is deregistered everywhere automatically and no orphan references remain in observability or allowlist

### Requirement: Auto-Discovery With Controlled Enrollment
The registry SHALL reconcile Herdr pane discovery with controlled enrollment so that phantom
panes from other workspaces never silently become managed agents, while legitimate new panes can
be enrolled in one step.

#### Scenario: Phantom pane rejected automatically
- **WHEN** a pane from a non-enrolled workspace appears in Herdr discovery
- **THEN** the registry ignores it by default (no DB write) without operator intervention

#### Scenario: Legitimate pane enrolled
- **WHEN** an operator enrolls a discovered pane
- **THEN** it becomes a managed agent and propagates to all consumers automatically

### Requirement: Stable Identity Across Pane Churn
Because Herdr pane IDs (e.g. `w6:p1`) can change/compact, the registry SHALL assign a stable
internal agent identity and map it to the current pane, so agent history, cost attribution, and
traces survive pane churn.

#### Scenario: Pane ID changes but identity persists
- **WHEN** an agent's underlying Herdr pane ID changes
- **THEN** the stable internal identity is preserved and all history/cost/traces remain linked to it
