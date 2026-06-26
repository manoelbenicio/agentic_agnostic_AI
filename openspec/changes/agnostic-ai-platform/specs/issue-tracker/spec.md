## ADDED Requirements

### Requirement: Issue List with Multiple View Modes
The system SHALL provide an Issue Tracker accessible at `/[workspaceSlug]/issues` with four view modes: List (tabular), Board/Kanban (drag-and-drop columns by status), Swimlane (horizontal grouping), and Gantt (timeline bars). The active view mode SHALL persist per user in local storage.

#### Scenario: User switches to Board view
- **WHEN** user clicks the "Board" toggle in the issues header
- **THEN** issues render as Kanban columns grouped by status (Backlog, Todo, In Progress, In Review, Done, Cancelled)
- **THEN** drag-and-drop between columns updates the issue status via `PATCH /api/issues/:id`

#### Scenario: User applies Status filter
- **WHEN** user selects "In Progress" in the Status filter popover
- **THEN** only issues with status "in_progress" are displayed
- **THEN** the active filter is shown as a badge on the filter button

### Requirement: Multi-Dimensional Filtering and Sorting
Issues SHALL be filterable by: Status (multi-select), Priority (multi-select), Assignee (human members and AI agents), Project, and free-text search (title/description match). Issues SHALL be sortable by: Title, Identifier, Status, Priority, Assignee, Created, Updated, Due Date.

#### Scenario: Filter by Assignee (AI agent)
- **WHEN** user opens the Assignee filter and selects an AI agent entry (robot badge indicator)
- **THEN** only issues assigned to that agent are shown

#### Scenario: Sort by Due Date ascending
- **WHEN** user selects "Due Date" ascending in Sort By dropdown
- **THEN** issues render ordered by `due_date ASC NULLS LAST`

### Requirement: Bulk Selection and Batch Actions
The system SHALL support multi-select via checkboxes. Selecting any issue checkbox SHALL render a BatchActionToolbar at the bottom of the view with actions: Change Status, Change Priority, Change Assignee, Delete.

#### Scenario: Bulk status change
- **WHEN** user selects 3 issues and clicks "Change Status → Done" in the batch toolbar
- **THEN** all 3 issues are updated to "done" via `PATCH /api/issues/bulk`
- **THEN** the selection is cleared and the toolbar dismisses

### Requirement: Right-Click Context Menu
Right-clicking on any issue row/card SHALL display a context menu with: Edit, Assign to Me, Change Status, Change Priority, Copy Link, Delete.

#### Scenario: Copy link from context menu
- **WHEN** user right-clicks an issue and selects "Copy Link"
- **THEN** the issue's canonical URL (`/[workspaceSlug]/issues/[identifier]`) is copied to the clipboard

### Requirement: Status and Priority Icon Systems
The system SHALL render 6 status icons as SVG circular progress rings: Backlog (dotted empty), Todo (empty + center dot), In Progress (half-filled + spinning animation when agent active), In Review (75% filled), Done (full green + checkmark), Cancelled (crossed circle). Priority SHALL render 4-bar vertical charts: No Priority (0/4 gray), Low (1/4), Medium (2/4 amber), High (3/4 orange), Urgent (4/4 red).

#### Scenario: In Progress with active agent
- **WHEN** an issue has status "in_progress" and an AI agent is actively assigned
- **THEN** the In Progress icon animates with a spinning dot
- **THEN** the issue row shows the agent avatar with a live activity ping indicator
