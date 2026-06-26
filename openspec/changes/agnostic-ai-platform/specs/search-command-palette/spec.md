## ADDED Requirements

### Requirement: Global Command Palette
The system SHALL provide a global command palette triggered by `Cmd+K` (macOS) or `Ctrl+K` (Windows/Linux), or by clicking the Search button in the sidebar. The palette SHALL render as a centered dialog overlay (Radix Dialog + cmdk primitive) with a text input (placeholder: "Type a command or search...") and `ESC` key badge.

#### Scenario: Open palette via keyboard shortcut
- **WHEN** user presses Ctrl+K anywhere in the application
- **THEN** the command palette dialog opens with focus on the search input
- **THEN** pressing Escape closes the palette without side effects

### Requirement: Search Result Types — 6 Categories
Search results SHALL be grouped dynamically: Pages (navigation links to Inbox, My Issues, Issues, Projects, Skills, Settings), Commands (New Issue, New Project, Copy Issue Link, Copy Identifier, Theme toggle), Members (by name/email/role, Pinyin matching for Chinese names), Projects (by name/description), Issues (by title/description/identifier/comments — showing ID, status icon, title, assignee, match snippet), Recent (empty query shows recently visited issues).

#### Scenario: Issue search with highlight
- **WHEN** user types "authentication" in the palette
- **THEN** matching issues appear with the word "authentication" highlighted in the title/description snippet
- **THEN** the issue's status icon, identifier (e.g. `AGN-42`), and assignee avatar are shown

#### Scenario: Recent items on empty query
- **WHEN** user opens the palette without typing
- **THEN** recently visited issues are shown in a "Recent" section (max 5 items)

### Requirement: Debounce and Request Cancellation
Search queries SHALL be debounced by 300ms. In-flight API requests SHALL be cancelled via `AbortController` when the user types further before the debounce fires. All match text SHALL be highlighted using a HighlightText component.

#### Scenario: Rapid typing cancels previous requests
- **WHEN** user types "auth" then immediately "authen"
- **THEN** the request triggered by "auth" is aborted
- **THEN** only the results for "authen" are displayed

### Requirement: Keyboard Navigation
Arrow keys (↑/↓) SHALL navigate between items in the result list. Enter SHALL trigger the selected item's action. Items SHALL have visible focus indicators when selected via keyboard.

#### Scenario: Navigate and select via keyboard
- **WHEN** user presses ↓ to select "New Issue" command
- **THEN** "New Issue" receives a visible focus ring
- **THEN** pressing Enter opens the New Issue modal
