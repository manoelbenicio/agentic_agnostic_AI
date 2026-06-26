## ADDED Requirements

### Requirement: Multi-Tenant Isolation
The platform SHALL isolate tenants such that seats, projects, issues, costs, and topologies
of one tenant are never visible or usable by another.

#### Scenario: Tenant data isolation
- **WHEN** a user of tenant X queries resources
- **THEN** only tenant X's seats, projects, issues, and costs are returned

### Requirement: Seat-Based Authentication
The system SHALL authenticate agent seats via OAuth / device-auth and MUST support multiple
subscriptions of the same vendor without overwriting each other's sessions.

#### Scenario: Multiple same-vendor subscriptions
- **WHEN** a tenant configures 5 Codex seats + 5 Antigravity seats + 5 Kiro seats
- **THEN** each seat authenticates independently and no seat's session overwrites another's

#### Scenario: Device-auth login
- **WHEN** a seat is enrolled via device-auth/OAuth
- **THEN** the credential is stored in the per-tenant seat vault and bound to that seat only

### Requirement: Role-Based Access Control
The platform SHALL enforce RBAC for human users (e.g., admin, operator, viewer) over
tenant resources and configuration.

#### Scenario: Viewer cannot modify seats
- **WHEN** a viewer attempts to enroll or release a seat
- **THEN** the action is denied by RBAC and audited
