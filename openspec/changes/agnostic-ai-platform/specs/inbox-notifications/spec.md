## ADDED Requirements

### Requirement: Inbox Layout — Resizable Panels
The Inbox SHALL render at `/[workspaceSlug]/inbox` as a two-column resizable layout (ResizablePanelGroup). Left panel (notification list, default 320px, min 240px, max 480px) and Right panel (detail view, min 40%). On mobile, the list renders fullscreen; selecting a notification renders the detail view overlaying the list with a "Back" button.

#### Scenario: Desktop inbox layout
- **WHEN** user navigates to Inbox on a desktop viewport (≥1024px)
- **THEN** the two-column resizable layout renders with the notification list on the left
- **THEN** the panel handle is draggable to resize within the min/max constraints

### Requirement: Notification Types — 13 Events
The system SHALL support and render 13 notification event types: `issue_assigned`, `issue_subscribed`, `unassigned`, `assignee_changed`, `status_changed`, `priority_changed`, `start_date_changed`, `due_date_changed`, `new_comment`, `mentioned`, `review_requested`, `task_completed`, `task_failed`, `agent_blocked`, `agent_completed`, `reaction_added`, `quick_create_done`, `quick_create_failed`. Each type SHALL display a distinct icon and action description.

#### Scenario: Agent blocked notification
- **WHEN** an AI agent reports it is blocked and requires human intervention
- **THEN** an `agent_blocked` notification is created in the inbox
- **THEN** the notification renders with a warning icon and "Agent requires your input" action text

### Requirement: Read/Unread State Management
Unread notifications SHALL display a 6px filled blue circle (`#3B82F6`), bold subject text (`font-medium`), and full opacity metadata. Read notifications SHALL have no circle, normal weight subject (`font-normal`), and 60% opacity metadata. Selecting a notification in the detail panel SHALL auto-mark it as read.

#### Scenario: Auto-mark-read on selection
- **WHEN** user clicks a notification in the left panel
- **THEN** the notification is immediately marked as read server-side via `PATCH /api/notifications/:id/read`
- **THEN** the blue unread indicator disappears within 100ms

### Requirement: Bulk Inbox Actions
The inbox header dropdown SHALL provide bulk actions: Mark all as read, Archive all, Archive all read, Archive completed (agent task completion notifications).

#### Scenario: Archive all read
- **WHEN** user selects "Archive all read" from the bulk actions dropdown
- **THEN** all notifications with `read: true` are archived via `POST /api/notifications/bulk-archive`
- **THEN** the notification list refreshes showing only unread items
