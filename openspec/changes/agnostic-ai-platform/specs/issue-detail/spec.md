## ADDED Requirements

### Requirement: Issue Detail Split Layout
The system SHALL render issue detail at `/[workspaceSlug]/issues/[identifier]` as a two-column split: Left column (description + activity timeline) and Right column (properties sidebar). Both columns SHALL be independently scrollable.

#### Scenario: User opens issue detail
- **WHEN** user clicks on an issue row or card
- **THEN** the split layout renders with breadcrumbs (`Workspace > Project > MUL-128 > Title`) at the top
- **THEN** the right sidebar shows current Status, Priority, Assignee, Labels, Due Date, Start Date, Project, and Sub-issues

### Requirement: TipTap Rich Text Description Editor
The description field SHALL use TipTap (ProseMirror) rich text editor supporting: inline markdown compilation, bullet/numbered lists, blockquotes, code blocks, file attachments, and `@mentions` of humans and agents.

#### Scenario: User @mentions an agent
- **WHEN** user types `@` in the description editor
- **THEN** a popover appears listing workspace members and AI agents (with robot badge)
- **THEN** selecting an agent inserts `@agent-name` as a linked mention token

### Requirement: Activity Timeline
The left column SHALL render a chronological timeline of: comments (with markdown rendering), status change events, assignment changes, priority changes, and agent activity entries. Each entry MUST show: actor avatar, actor name, action description, and relative timestamp.

#### Scenario: Status change appears in timeline
- **WHEN** an issue status changes from "Todo" to "In Progress"
- **THEN** a timeline entry appears: `[Avatar] [UserName] changed status from Todo to In Progress · 2m ago`

### Requirement: Agent Working Live Panel
When an AI agent is assigned to an issue and is actively processing, the system SHALL render a live panel in the left column showing: rotating spinner, "Agent is working..." label, elapsed execution timer (live, seconds granularity), and an expandable list of current tool invocations (shell commands, file reads, API calls).

#### Scenario: Agent working panel visible
- **WHEN** an agent's task status is "running" on an assigned issue
- **THEN** the Agent Working Live Panel renders with real-time updates via WebSocket
- **THEN** each tool invocation appears as a new log entry within ~500ms of execution

#### Scenario: Agent completes task
- **WHEN** the agent finishes and closes the task
- **THEN** the live panel transitions to a "Completed" state showing total elapsed time
- **THEN** a timeline entry is added with "Agent completed task"

### Requirement: Execution Log Section
The system SHALL render an Execution Log Section below the activity timeline, collapsible, showing: all agent tool calls with inputs/outputs, thinking logs (chain-of-thought), and error messages with stack traces if applicable.

#### Scenario: User expands execution log
- **WHEN** user clicks to expand the Execution Logs section
- **THEN** all tool calls from the current agent session are listed chronologically
- **THEN** shell command entries show the exact command run and stdout/stderr output

### Requirement: Properties Sidebar Pickers
The right column SHALL provide inline pickers for: Status (dropdown), Priority (dropdown), Assignee (searchable popover showing human members and agents with robot badges), Labels (multi-select tag popover), Due Date/Start Date (calendar popover), Project (select dropdown), and Sub-issues / Parent Issue (hierarchical selector).

#### Scenario: Assign issue to AI agent
- **WHEN** user opens Assignee picker and selects an AI agent
- **THEN** the backend triggers an agent assignment webhook
- **THEN** the issue status transitions to "In Progress" automatically
- **THEN** the Agent Working Live Panel activates
