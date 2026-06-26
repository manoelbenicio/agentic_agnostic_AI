## ADDED Requirements

### Requirement: Device Authorization Request
The system SHALL implement OAuth 2.0 Device Authorization Grant (RFC 8628). When a user initiates login, the backend MUST issue a `device_code`, `user_code`, and `verification_uri`. The user code SHALL be displayed in the UI (format: `XXXX-YYYY`). The `verification_uri` SHALL be the Google/Microsoft SSO authorization endpoint.

#### Scenario: User initiates device login
- **WHEN** user opens the app and clicks "Sign In"
- **THEN** the frontend calls `POST /auth/device/authorize` and receives `{ device_code, user_code, verification_uri, expires_in, interval }`
- **THEN** the UI displays the `user_code` and a QR code linking to `verification_uri`

#### Scenario: User code expires before authorization
- **WHEN** the device code TTL elapses (default: 900 seconds) without user authorization
- **THEN** the frontend displays "Session expired. Please try again." and resets to the initial login screen

### Requirement: Backend Token Polling
The frontend SHALL poll `POST /auth/device/token` at the interval returned by the device authorization response. The backend MUST respond with `authorization_pending` while the user has not approved, `access_denied` if rejected, or a JWT access token on success.

#### Scenario: Successful authorization
- **WHEN** user approves the device login in their browser
- **THEN** the next poll returns `{ access_token, token_type: "Bearer", expires_in }` (JWT, stateless)
- **THEN** the frontend stores the JWT in an httpOnly cookie and redirects to the workspace dashboard

#### Scenario: Authorization denied by user
- **WHEN** user rejects the authorization request in their browser
- **THEN** the backend responds with `{ error: "access_denied" }`
- **THEN** the frontend displays "Authorization denied." and stops polling

### Requirement: JWT Stateless Sessions
All API calls after authentication SHALL include the JWT as `Authorization: Bearer <token>`. The backend MUST validate JWT signature and expiry on every request. No server-side session state SHALL be required.

#### Scenario: Expired JWT access
- **WHEN** a request is made with an expired JWT
- **THEN** the backend returns HTTP 401 with `{ error: "token_expired" }`
- **THEN** the frontend triggers a silent re-authentication flow (Device Flow again)

### Requirement: Google SSO Integration
The OAuth Device Flow SHALL support Google as the identity provider. The backend MUST use Google's Device Authorization endpoint (`https://oauth2.googleapis.com/device/code`). Scopes: `openid email profile`.

#### Scenario: Google account linked to workspace
- **WHEN** user approves via Google SSO
- **THEN** the backend creates or updates the user record with Google `sub` identifier and email
- **THEN** a JWT is issued with `user_id`, `workspace_slug`, `email`, `roles` claims

### Requirement: Zero API Key Exposure
The system MUST NOT require users to enter, store, or manage LLM API Keys. All LLM credentials SHALL be stored server-side in environment variables accessible only to the backend service.

#### Scenario: User attempts to configure LLM key in UI
- **WHEN** a user navigates to any settings screen
- **THEN** NO input field for API Keys SHALL be present
- **THEN** LLM provider selection (if exposed) SHALL be workspace-admin-only and credential-free from the user's perspective
