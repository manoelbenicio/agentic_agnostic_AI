## ADDED Requirements

### Requirement: Granular Communication Topology
When building a squad or a project, the system SHALL allow defining, at a granular level,
**which agent may communicate with which** (directed allow-list of communication edges).
The canvas connection lines between agent nodes ARE the authoritative communication
topology.

#### Scenario: Define who talks to whom in the squad builder
- **WHEN** a user connects agent A → agent B on the Visual Squad Builder canvas
- **THEN** the system records a directed permission allowing A to send messages/handoffs to B
- **THEN** no edge between two agents means communication between them is denied by default (default-deny)

#### Scenario: Project-level topology overrides
- **WHEN** a project defines its own communication topology
- **THEN** tasks within that project enforce the project topology for their agents

### Requirement: Runtime Enforcement Of Topology
The control plane MUST enforce the defined topology at runtime. Any `send_message`,
`handoff`, or `assign` action between agents that is NOT permitted by the topology SHALL
be blocked and audited.

#### Scenario: Disallowed message blocked
- **WHEN** agent C attempts to send a message to agent D and no A→B style edge C→D exists
- **THEN** the message is rejected with a topology-violation error
- **THEN** the violation is recorded in the audit log with `trace_id`, source, target, and action

#### Scenario: Allowed handoff proceeds
- **WHEN** agent A hands off to agent B and edge A→B exists
- **THEN** the handoff is permitted and emitted as a normal lifecycle event

### Requirement: Topology Roles And Directionality
The topology SHALL support directional edges and role semantics (e.g., Tech-Lead → worker
fan-out, worker → Tech-Lead report-back) so that broadcast, delegation, and review paths
can be modeled distinctly.

#### Scenario: Tech-Lead fan-out path
- **WHEN** a Tech-Lead node has outgoing edges to three worker nodes
- **THEN** the Tech-Lead may dispatch to all three, but the workers may only talk back along defined return edges

### Requirement: Default Hub-and-Spoke Authority
By default, the designated Tech-Lead SHALL have full authority: it MAY communicate with and
manage all agents, and all agents MAY communicate with the Tech-Lead. **Agents MUST NOT
communicate with one another by default** — lateral agent-to-agent communication is denied
unless the Tech-Lead explicitly grants it (an explicit allowed edge).

#### Scenario: Default topology applied to a new squad
- **WHEN** a squad is created with a designated Tech-Lead and no custom edges
- **THEN** every agent ↔ Tech-Lead path is allowed (both directions)
- **THEN** every agent ↔ agent path is denied by default

#### Scenario: Agent attempts lateral communication without grant
- **WHEN** agent A1 tries to message agent A2 and the Tech-Lead has not granted an A1→A2 edge
- **THEN** the message is blocked as a topology violation and audited

#### Scenario: Tech-Lead grants a lateral edge
- **WHEN** the Tech-Lead explicitly grants A1 → A2 communication
- **THEN** an allowed directed edge A1→A2 is created and A1 may message A2
- **THEN** revoking the grant returns A1→A2 to denied

#### Scenario: Tech-Lead manages any agent
- **WHEN** the Tech-Lead issues a manage/dispatch/handoff to any agent in the squad
- **THEN** the action is permitted regardless of lateral restrictions

### Requirement: Customer-Facing Topology Customization Tools
Customers SHALL be given first-class tools, when building squads and projects, to define and
fully customize the communication topology (who can talk to whom) at a granular level. The
default hub-and-spoke policy is only a starting point and MUST be entirely overridable by the
customer.

#### Scenario: Customer overrides the default topology
- **WHEN** a customer opens the topology tools for a squad with the default hub-and-spoke applied
- **THEN** the customer can add, remove, and direct any communication edge between any agents
- **THEN** the customized topology replaces the default and is enforced at runtime

#### Scenario: Customer builds a fully custom mesh
- **WHEN** a customer explicitly defines lateral edges among several agents
- **THEN** exactly those lateral paths are allowed and all others remain denied (default-deny)

#### Scenario: Per-project vs per-squad customization
- **WHEN** a customer customizes topology at both squad and project scope
- **THEN** the system applies the documented precedence (project scope overrides squad default) and shows the effective topology

### Requirement: Enforcement Reuses HerdMaster AclEngine
The runtime enforcement of communication topology SHALL reuse the existing HerdMaster
`AclEngine` (default-deny policy with roles such as orchestrator/worker/peer_reviewer/observer)
as the authoritative backend. The Visual Squad Builder edges and roles MAP to AclEngine config
(`role`, `can_send_to`, `can_dispatch`, `can_reassign`); the platform MUST NOT implement a
parallel, divergent ACL.

#### Scenario: Canvas edge maps to ACL config
- **WHEN** a user assigns the Tech-Lead role to an agent and connects it to workers on the canvas
- **THEN** the platform writes the equivalent AclEngine roles (orchestrator + workers, default-deny) so enforcement is identical to the existing control plane

#### Scenario: Default-deny inherited from AclEngine
- **WHEN** no explicit edge/permission exists between two agents
- **THEN** the AclEngine default-deny policy blocks the communication without additional configuration

### Requirement: Topology Validation
The system SHALL validate a defined topology before activation, rejecting configurations
that violate structural rules (e.g., an isolated agent with no path, or a disallowed cycle
where the policy forbids it).

#### Scenario: Invalid topology rejected
- **WHEN** a user activates a squad whose topology leaves a mandatory coordinator unreachable
- **THEN** activation is blocked with a clear validation message identifying the offending nodes
