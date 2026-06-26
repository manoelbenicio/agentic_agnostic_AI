## ADDED Requirements

### Requirement: Dual Cost Engine
The FinOps module SHALL compute cost through two engines: (a) **token-based** for
API-backed runs (tokens × model price) and (b) **seat-utilization-based** for flat-rate
subscription seats (fixed cost amortized over utilization).

#### Scenario: Token-based cost
- **WHEN** a task runs via an API-backed adapter reporting token usage
- **THEN** FinOps computes cost as tokens × model unit price and records it

#### Scenario: Seat-utilization cost
- **WHEN** a task runs on a flat-rate subscription seat
- **THEN** FinOps records seat-utilization (seat-minutes / share of the period) rather than token cost

### Requirement: Hierarchical Cost Attribution
Every cost/utilization unit MUST be tagged along the chain `tenant → project → issue →
agent → runtime` so cost can be aggregated at any level.

#### Scenario: Cost rollup by project
- **WHEN** an operator queries the cost of a project
- **THEN** FinOps aggregates all tagged units across issues/agents/runtimes for that project

### Requirement: Utilization Insight For Seats
For subscription seats, FinOps SHALL answer "am I utilizing what I pay for?" by reporting
idle-seat detection and seat right-sizing recommendations.

#### Scenario: Idle seat detected
- **WHEN** a paid seat goes unused beyond a threshold within the billing period
- **THEN** FinOps flags the idle seat and suggests right-sizing

### Requirement: Billing Modes
The platform SHALL support both **pay-as-you-go** and **monthly** billing modes per tenant.

#### Scenario: Pay-as-you-go accrual
- **WHEN** a tenant is on pay-as-you-go
- **THEN** costs accrue per usage and are billable on demand

#### Scenario: Monthly plan
- **WHEN** a tenant is on a monthly plan
- **THEN** usage is metered against the plan and overage is reported
