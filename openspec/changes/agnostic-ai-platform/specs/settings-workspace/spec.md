## ADDED Requirements

### Requirement: Settings — Ten Tabs
The system SHALL provide a Settings area accessible at `/[workspaceSlug]/settings` with ten tab sections: General, Members, Repositories, GitHub, Integrations, Profile, Preferences, Notifications, API Tokens, Labs.

#### Scenario: Tab navigation
- **WHEN** user clicks any settings tab
- **THEN** the URL updates to `/settings?tab=<tab-name>` and the tab content renders
- **THEN** unsaved changes in the current tab trigger a "You have unsaved changes" warning before navigating away

### Requirement: General Tab
General tab SHALL have: Logo Upload (PNG/JPEG/WEBP, Admin/Owner only), Name Input, Description Textarea, Context Textarea (AI agent background info, placeholder "Background information and context for AI agents working in this workspace"), Slug Input (read-only), Issue Prefix Input (2-10 uppercase alphanumeric chars). Changing issue prefix SHALL trigger a warnings dialog listing renumbering impact.

#### Scenario: Issue prefix change warning
- **WHEN** admin changes issue prefix from "MUL" to "AGN" and saves
- **THEN** a modal warns: "All issues will be renumbered from MUL-N to AGN-N. External references will stop resolving."
- **THEN** user must click "Confirm" to proceed

### Requirement: Members Tab
Members tab SHALL have: Invite Member form (email input + role dropdown: Member/Admin), Members List (avatar, name, email, role badge, join date, role management dropdown), Owner Constraint (last owner cannot be demoted), Remove Member (confirmation dialog), Pending Invitations list (email, status, role, Revoke button).

#### Scenario: Invite member
- **WHEN** admin enters an email and selects "Admin" role, then clicks "Invite"
- **THEN** an invitation is created and appears in the Pending Invitations list
- **THEN** the invitee receives an email with the workspace join link

### Requirement: API Tokens Tab
API Tokens tab SHALL allow: Create token (Name input, Expiry select: 30 days/90 days/1 year/No expiry), token list display (name, masked prefix `mt_...`, created date, last used, expiry), one-time token reveal dialog on creation ("Copy your personal access token now. You won't be able to see it again."), Revoke button (confirmation dialog).

#### Scenario: Token created and revealed once
- **WHEN** user creates a token named "My CLI" with 90-day expiry
- **THEN** a dialog shows the full raw token string with copy button and warning text
- **THEN** after closing the dialog, the token is masked as `mt_xxxx...` in the list and never shown in full again

### Requirement: Preferences Tab
Preferences tab SHALL have: Theme selection (Light/Dark/System radio cards — System preview shows diagonal split), Language selector (English/中文/한국어/日本語 — changing writes cookie + patches backend + reloads page), Timezone selector (full IANA timezone list, default `__browser__`).

#### Scenario: Language switch to Chinese
- **WHEN** user selects "中文" in the language selector
- **THEN** the preference is saved to backend and a language cookie is set
- **THEN** the page reloads with all UI strings rendered in Simplified Chinese

### Requirement: Notifications Tab
Notifications tab SHALL have toggles for: Assignments, Status Changes, Comments & Mentions, Priority & Due Date, Agent Activity (inbox notification categories), and System Notifications toggle (native OS banners). Browser Notifications card showing current permission status (granted/denied/default).

#### Scenario: Agent Activity notifications disabled
- **WHEN** user toggles off "Agent Activity"
- **THEN** no inbox notifications are created for agent task completion or failure events
