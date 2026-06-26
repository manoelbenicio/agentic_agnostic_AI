## ADDED Requirements

### Requirement: Agnostic Runtime Interface
The system SHALL define a single agent runtime interface with operations
`spawn`, `send`, `readState`, `stop`, `restore`, and `meter`. Every supported agent CLI
(Codex, Kiro, Antigravity, Gemini, Cursor, and others) MUST be integrated as an adapter
implementing this interface. The existing HerdMaster `HerdrAdapter` (agent_list, pane_read,
pane_send, agent_wait, spawn_agent) SHALL be the reference implementation for Terminal-mode
execution and MUST be generalized to fit this interface rather than re-implemented.

#### Scenario: New vendor added via adapter
- **WHEN** a new agent CLI adapter implementing the interface is registered
- **THEN** the orchestrator can spawn and control it without changes to the brain or executors

#### Scenario: Adapter reports normalized state
- **WHEN** `readState` is called on any adapter
- **THEN** it returns one of the normalized states `idle | working | blocked | done | unknown`

### Requirement: Native State Detection With Scrape Fallback
Adapters MUST provide native/semantic state detection where the vendor supports it, and
SHALL fall back to terminal screen-scrape heuristics when no native signal exists.

#### Scenario: Native adapter available
- **WHEN** a vendor exposes a semantic state hook
- **THEN** the adapter uses the native signal as the authoritative state source

#### Scenario: Fallback to scrape
- **WHEN** no native signal is available for a CLI
- **THEN** the adapter derives state from foreground process name + terminal output heuristics

### Requirement: Metering Hook
Each adapter MUST expose a `meter` hook that reports usage units relevant to its billing
model (tokens for API-backed runs, seat-seconds/seat-minutes for subscription seats).

#### Scenario: Seat-based metering
- **WHEN** a subscription-seat agent runs a task
- **THEN** the adapter reports seat-utilization units (not token counts) to FinOps
