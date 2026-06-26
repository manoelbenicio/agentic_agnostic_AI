## ADDED Requirements

### Requirement: Projects List with Progress Cards
The system SHALL render a projects dashboard at `/[workspaceSlug]/projects` showing project cards in a grid/list layout. Each card MUST display: project icon, title, description, lead member avatar, progress bar (completed/total issues percentage), and status tag (Active, Paused, Completed).

#### Scenario: Projects dashboard loads
- **WHEN** user navigates to `/[workspaceSlug]/projects`
- **THEN** all workspace projects render as cards with real-time progress bars
- **THEN** a "+ New Project" button is visible in the header

### Requirement: Project Creation Modal
Clicking "+ New Project" SHALL open a modal dialog with fields: Project Name (required), Project Key (required, 2-5 uppercase chars, used as issue prefix e.g. `MUL`), Description (optional), Project Lead (member select dropdown), Color Picker (circular swatches). The submit button SHALL be disabled until Name and Key are filled.

#### Scenario: Project key conflict
- **WHEN** user enters a Project Key already used by another project
- **THEN** an inline validation error appears: "This key is already in use."
- **THEN** the submit button remains disabled

### Requirement: Project Detail with Scoped Issues
Each project SHALL have a detail page at `/[workspaceSlug]/projects/[id]` displaying: Title, Key, Lead Member, Description, Local Directory Path (on-disk path used by agents), associated git repository. The page SHALL embed a scoped Issue Tracker filtered to only issues belonging to that project.

#### Scenario: Agent uses project directory path
- **WHEN** an agent is assigned an issue within a project
- **THEN** the agent receives the project's `local_directory_path` as its working directory for code execution
