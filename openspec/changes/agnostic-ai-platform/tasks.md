## 1. Docker Infrastructure & Base Setup

- [ ] 1.1 Create `docker-compose.yml` defining frontend, backend, postgres, redis, prometheus, grafana, blackbox-exporter on `agnosticai_net`.
- [ ] 1.2 Configure network isolation (DB ports only exposed if `EXPOSE_DB_PORTS=true`).
- [ ] 1.3 Setup `.env` file template with required secrets (DB, JWT, Google OAuth, Litellm API keys).
- [ ] 1.4 Implement backend startup script to run Alembic migrations automatically before accepting requests.

## 2. Observability Stack

- [ ] 2.1 Implement `/metrics` Prometheus endpoint in FastAPI backend exposing custom counters.
- [ ] 2.2 Implement `/health` and `/health/ready` liveness/readiness endpoints (checking DB and Redis).
- [ ] 2.3 Provision initial Grafana dashboards JSON (`agnosticai_main.json`) in deployment folder.
- [ ] 2.4 Configure Prometheus `alert_rules.yml` for BackendNotReady, HighErrorRate, and LLMHighLatency.

## 3. Backend LLM Router

- [ ] 3.1 Implement litellm wrapper for agnostic provider routing (`POST /api/llm/complete`).
- [ ] 3.2 Implement model fallback mechanism for rate limits (429) or 5xx errors.
- [ ] 3.3 Add token tracking metrics via `litellm.success_callback` (incrementing Prometheus counters).
- [ ] 3.4 Configure Server-Sent Events (SSE) streaming for LLM responses to frontend.

## 4. Authentication (OAuth Device Flow)

- [ ] 4.1 Implement `POST /auth/device/authorize` endpoint to generate device code and user code.
- [ ] 4.2 Implement `POST /auth/device/token` endpoint for frontend polling.
- [ ] 4.3 Configure Google SSO identity provider integration for device flow.
- [ ] 4.4 Implement JWT issuing, validation middleware, and stateless session handling.
- [ ] 4.5 Build frontend Device Login UI (QR code, user code display, polling logic).

## 5. Design System & Layout Foundation

- [ ] 5.1 Define OKLCH color tokens for Light and Dark modes in Tailwind config / CSS variables.
- [ ] 5.2 Configure Typography scale (Inter, Source Serif 4, Geist Mono).
- [ ] 5.3 Configure border radius, spacing tokens, and container max-widths.
- [ ] 5.4 Implement base layout skeleton, sidebar, and Next-themes provider.
- [ ] 5.5 Create reusable status SVG icons and priority vertical charts components.
- [ ] 5.6 Implement Cmd+K Search Command Palette (cmdk) with 6 grouped categories and debounced fetching.

## 6. Workspace Settings

- [ ] 6.1 Implement Settings layout with 10 side-tabs routing.
- [ ] 6.2 Build General tab (Name, Slug, Issue Prefix with renumbering warning).
- [ ] 6.3 Build Members tab (Invite form, Members list, Role management).
- [ ] 6.4 Build API Tokens tab (Create, Revoke, one-time reveal dialog).
- [ ] 6.5 Build Preferences tab (Theme, Language, Timezone selectors).
- [ ] 6.6 Build Notifications tab (Event toggles).

## 7. Projects Manager

- [ ] 7.1 Build Projects List dashboard with progress cards and status tags.
- [ ] 7.2 Implement New Project modal (Key generation, validation, color picker).
- [ ] 7.3 Build Project Detail page showing metadata and local directory path.
- [ ] 7.4 Embed scoped issue tracker within Project Detail page.

## 8. Issue Tracker Views & Actions

- [ ] 8.1 Implement base Issue List (tabular) view.
- [ ] 8.2 Implement Board (Kanban) view with drag-and-drop status columns.
- [ ] 8.3 Implement Swimlane and Gantt timeline views.
- [ ] 8.4 Add multi-dimensional filtering (Status, Priority, Assignee) and sorting functionality.
- [ ] 8.5 Build Batch Action Toolbar for bulk status/priority/assignee/delete actions.
- [ ] 8.6 Implement right-click context menu on issue rows.

## 9. Issue Detail & Real-time Panels

- [ ] 9.1 Build Issue Detail split layout (Description/Timeline left, Properties right).
- [ ] 9.2 Implement TipTap rich text editor for description with @mentions support.
- [ ] 9.3 Build Activity Timeline rendering chronological events and comments.
- [ ] 9.4 Implement Properties Sidebar inline pickers (Status, Priority, Assignee, Labels, Dates).
- [ ] 9.5 Build Agent Working Live Panel with WebSocket streaming for real-time logs.
- [ ] 9.6 Build Execution Log section displaying detailed tool calls, outputs, and errors.

## 10. Inbox & My Issues

- [ ] 10.1 Implement Resizable Panel layout for Inbox (List left, Detail right).
- [ ] 10.2 Render 13 distinct notification event types with proper icons.
- [ ] 10.3 Implement Read/Unread state styling and auto-mark-read on click.
- [ ] 10.4 Build Inbox Header with bulk archive actions.
- [ ] 10.5 Build My Issues page with 4 Scope Tabs (All, Assigned, Created, My Agents).

## 11. Skills System

- [ ] 11.1 Build Skills List page with origin tags, assignments badges, and role-based permissions.
- [ ] 11.2 Implement New Skill modal (Manual, Import URL, Copy from Runtime flows).
- [ ] 11.3 Build Skill Detail Three-Column Editor (File Tree, Code Editor, Metadata).
- [ ] 11.4 Implement skill-agent assignment dropdown and batch linking.
