## ADDED Requirements

### Requirement: Skills List and Management
The system SHALL provide a Skills management page at `/[workspaceSlug]/skills` displaying all workspace skills. Each skill row MUST show: Name, Description, Origin (Manual/ClawHub/Skills.sh/GitHub), Creator avatar, Updated timestamp, and assignment count badge (e.g. `2/5 agents`). Only skill creators or Admins/Owners SHALL be able to edit or delete skills.

#### Scenario: Skills list renders with origins
- **WHEN** user navigates to the Skills page
- **THEN** skills are listed with visual distinction between Manual and imported (ClawHub/GitHub) origins
- **THEN** admin/owner users see Edit and Delete controls; regular members see view-only rows

### Requirement: Skill Creation — Three Methods
Clicking "+ New Skill" SHALL open a dialog offering three creation methods:

1. **Create Manually**: Name input (unique, validation), Description textarea. Submitting creates the skill and navigates to the Skill Detail editor.
2. **Import from URL**: URL input field. The backend MUST auto-detect source domain (clawhub.ai → ClawHub, skills.sh → Skills.sh, github.com → GitHub). Clicking "Import" fetches the skill package server-side.
3. **Copy from Runtime**: Runtime selection dropdown (only online runtimes). Skills list with checkboxes from the selected runtime. Single-skill selection expands inline edit for name/description. Batch import (up to 10 concurrent). Conflict resolution: Overwrite / Rename (default: append " copy") / Skip.

#### Scenario: Import from ClawHub URL
- **WHEN** user enters `https://clawhub.ai/owner/skill-name` and clicks "Import"
- **THEN** the backend fetches the skill package from ClawHub API
- **THEN** the skill appears in the list with `Origin: ClawHub` tag

#### Scenario: Name conflict during runtime copy
- **WHEN** user copies a runtime skill whose name already exists in the workspace
- **THEN** a conflict resolution card appears with Overwrite / Rename / Skip options
- **THEN** selecting "Rename" pre-fills the new name field with `original-name copy`

### Requirement: Skill Detail Editor — Three-Column Layout
The skill detail page SHALL render a three-column layout:
1. **Left: File Tree** — Lists skill files. `SKILL.md` is mandatory and un-deletable. "+ Add file" button with path validation (relative, no `..`, not `SKILL.md`, no duplicate).
2. **Center: Code Editor** — Name (inline editable, locked for non-owners), Description textarea, Metadata subline (origin, updated time, creator avatar/name), Conflict Invalidation Banner (concurrent edit warning), Code Editor (markdown preview or raw), Save Bar anchored at bottom when changes exist ("Unsaved changes — will overwrite the live skill on save" + Discard/Save buttons).
3. **Right: Metadata & Assignments** — ID, Origin info, Created/Updated dates, Permissions info block, "Used By" section listing assigned agents (or "Not assigned to any agent yet." empty state).

#### Scenario: Concurrent edit conflict
- **WHEN** another user saves the same skill while the current user has unsaved changes
- **THEN** a warning banner appears: "Someone else updated this skill. Your edits are preserved. Discard to pull their changes, or Save to overwrite."

### Requirement: Skill-Agent Assignment
Skills SHALL be assignable to agents directly from the Skills list via an "Actions" row dropdown. The assignment list MUST group agents as "My agents" and "Other agents". Fractional count badges (e.g. `1/2 added`) SHALL indicate partial assignment. Selecting multiple skills SHALL activate a Batch Toolbar for bulk Add to Agent or Delete operations.

#### Scenario: Assign skill to agent from list
- **WHEN** user opens the Actions dropdown for a skill and selects an agent
- **THEN** the skill is linked to the agent in the database
- **THEN** the assignment badge updates to reflect the new count
