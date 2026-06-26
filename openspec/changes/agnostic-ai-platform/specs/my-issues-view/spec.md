## ADDED Requirements

### Requirement: My Issues Scope Tabs
The My Issues view at `/[workspaceSlug]/my-issues` SHALL provide four scope tabs: All (all issues related to the user), Assigned (directly assigned to logged-in user), Created (issues created by logged-in user), My Agents and Squads (issues assigned to user's AI agents or squads). The active tab SHALL be reflected in the URL query param `?scope=<tab>`.

#### Scenario: "My Agents and Squads" tab
- **WHEN** user clicks the "My Agents and Squads" tab
- **THEN** issues assigned to any AI agent owned by the logged-in user are displayed
- **THEN** a filter chip "Agents working" appears to further filter to only actively running agents

### Requirement: Three View Modes
My Issues SHALL support Board view (Kanban columns, drag-and-drop), List view (compact vertical list with BatchActionToolbar), and Swimlane view (horizontal lanes). View mode SHALL be toggled via header buttons and persisted per user.

#### Scenario: List view with batch actions
- **WHEN** user is in List view and selects multiple issue checkboxes
- **THEN** the BatchActionToolbar appears at the bottom with Change Status, Change Priority, Change Assignee, Delete actions

### Requirement: Grouping and Ordering
Display settings SHALL support Grouping (by Status or by Assignee) and Ordering (manual, ascending, descending). In Board view grouped by Assignee, each column/lane represents a single agent or team member.

#### Scenario: Board grouped by Assignee
- **WHEN** user sets Group By to "Assignee" in Board view
- **THEN** each Kanban column represents one assignee (human or agent avatar as column header)
- **THEN** issues with no assignee appear in an "Unassigned" column
