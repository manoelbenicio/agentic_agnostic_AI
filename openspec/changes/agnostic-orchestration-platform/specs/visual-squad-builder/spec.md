## ADDED Requirements

### Requirement: Drag-and-Drop Squad Composition
The Visual Squad Builder SHALL let users compose a squad from agent building blocks
(e.g., select 2 Codex + 2 Antigravity + 5 Gemini Flash) by dragging nodes onto a canvas,
implemented with `@xyflow/react`.

#### Scenario: Add agents as building blocks
- **WHEN** a user drags agent blocks onto the canvas and sets counts
- **THEN** the squad is composed with the chosen agents and persisted

### Requirement: Connection-Line Topology Editing
Users SHALL define communication paths by dragging connection lines between agent nodes.
These edges feed the `communication-topology-acl` capability as the authoritative
who-talks-to-whom definition.

#### Scenario: Draw a connection
- **WHEN** a user drags a line from agent A to agent B
- **THEN** a directed edge A→B is created and registered as an allowed communication path

#### Scenario: Remove a connection
- **WHEN** a user deletes the A→B edge
- **THEN** communication from A to B reverts to denied (default-deny)

### Requirement: Fluid Performance
Canvas interactions (drag, connect, pan, zoom, transitions) MUST remain smooth and
lag-free for typical squad sizes, with visual transition effects.

#### Scenario: Smooth interaction under typical load
- **WHEN** a squad with dozens of agent nodes is edited
- **THEN** drag/connect/pan/zoom remain responsive without perceptible lag

### Requirement: Optional Chatbot Entry Point
The builder SHALL offer an optional chatbot entry for users who do not want to wire blocks
manually; the chatbot proposes a squad and topology the user can then refine on the canvas.

#### Scenario: Chatbot-assisted squad
- **WHEN** a user describes a goal to the builder chatbot
- **THEN** the system proposes a squad + topology rendered on the canvas for editing
