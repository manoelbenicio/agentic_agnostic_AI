## ADDED Requirements

### Requirement: Quota-Aware Admission Control
The scheduler SHALL track shared subscription quota/burn per vendor (5-hour and weekly
caps) and MUST NOT dispatch work that would exceed available quota. Tasks are queued, not
failed, when quota is exhausted.

#### Scenario: Dispatch within quota
- **WHEN** a task is ready and the vendor's shared quota has headroom
- **THEN** the scheduler dispatches it and decrements the tracked burn estimate

#### Scenario: Quota exhausted
- **WHEN** the vendor's 5-hour or weekly quota is exhausted
- **THEN** new tasks for that vendor are queued and surfaced as `waiting_on_quota`

### Requirement: Backoff On Rate-Limit Responses
On receiving HTTP 429 or 503 from a vendor, the scheduler SHALL apply exponential backoff
with jitter before retrying, and SHALL not hammer the vendor.

#### Scenario: 503 from Antigravity
- **WHEN** a dispatch attempt returns 503
- **THEN** the scheduler backs off exponentially and retries later, logging the backoff window

### Requirement: Concurrency Ceiling
The scheduler SHALL enforce a configurable maximum concurrent task ceiling (default aligned
to ~20) to protect host resources and vendor limits.

#### Scenario: Concurrency cap reached
- **WHEN** the number of running tasks reaches the configured ceiling
- **THEN** additional ready tasks remain queued until a slot frees

### Requirement: Burn-Rate Forecasting
The scheduler SHALL expose a burn-rate estimate so operators can forecast quota
exhaustion before it happens.

#### Scenario: Burn-rate alert
- **WHEN** projected burn indicates the weekly cap will be hit ahead of schedule
- **THEN** an alert is emitted via the observability stack
