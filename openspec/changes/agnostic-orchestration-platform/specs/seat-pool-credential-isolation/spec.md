## ADDED Requirements

### Requirement: Per-Tenant Seat Pool
The system SHALL maintain a pool of authenticated seats per tenant and per vendor (e.g.,
N Codex seats, M Antigravity seats, K Kiro seats). Seats MUST be leased to agents and
released on completion or failure.

#### Scenario: Seat leased on dispatch
- **WHEN** an agent task is dispatched and a free seat exists for the requested vendor
- **THEN** the scheduler leases one seat and binds it to that agent process
- **THEN** the seat is marked unavailable until released

#### Scenario: No free seat
- **WHEN** all seats of a vendor are leased
- **THEN** the task is queued (not failed) until a seat is released

### Requirement: Credential Isolation Per Process
Each leased seat MUST run with an isolated credential sandbox (dedicated HOME/config
directory and environment) so that concurrent agents of the same vendor never overwrite
each other's authentication session.

#### Scenario: Two same-vendor agents run concurrently
- **WHEN** two Codex agents run at the same time on different seats
- **THEN** each uses its own isolated config/HOME and neither clobbers the other's OAuth/device-auth session

#### Scenario: Session preserved across concurrent logins
- **WHEN** multiple seats authenticate via device-auth/OAuth
- **THEN** no seat's session is overwritten by another (validated behavior from the customized Herdr fork)

### Requirement: Subagents Inherit Parent Seat
Subagents spawned by an agent SHALL run within the parent agent's seat (same session),
as short-lived helpers. The seat pool size MUST be sized by parent-agent count, not by
subagent count.

#### Scenario: Tech-Lead spawns subagents
- **WHEN** a coordinator agent spawns 2–3 subagents
- **THEN** those subagents reuse the parent's seat and do not consume additional pool seats

### Requirement: Lease Affinity And Refresh
Long-running tasks SHALL retain their seat (affinity). The system MUST refresh/rotate
seat tokens that expire and return healthy seats to the pool on release.

#### Scenario: Token expiry during a long task
- **WHEN** a seat's auth token approaches expiry mid-task
- **THEN** the system refreshes the token without dropping the running agent
