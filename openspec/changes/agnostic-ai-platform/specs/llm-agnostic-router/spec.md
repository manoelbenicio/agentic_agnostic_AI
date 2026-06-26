## ADDED Requirements

### Requirement: Agnostic LLM Provider Routing
The backend SHALL route LLM requests to the configured provider (OpenAI, Anthropic, Google Gemini) transparently, using `litellm` as the abstraction layer. The frontend SHALL never send API credentials to any LLM provider directly. All LLM calls MUST go through `POST /api/llm/complete`.

#### Scenario: Request to OpenAI via router
- **WHEN** a request arrives at `POST /api/llm/complete` with `{ model: "gpt-4o", messages: [...] }`
- **THEN** the backend routes via litellm to OpenAI using server-side credentials
- **THEN** the response is streamed back to the frontend via SSE (Server-Sent Events)

#### Scenario: Request to Anthropic via router
- **WHEN** a request arrives with `{ model: "claude-3-5-sonnet-20241022", messages: [...] }`
- **THEN** litellm routes to Anthropic Claude API transparently
- **THEN** response streams back identically to OpenAI responses

#### Scenario: Unsupported model requested
- **WHEN** a model string not in the allowed list is provided
- **THEN** the backend returns HTTP 400 with `{ error: "model_not_supported", allowed_models: [...] }`

### Requirement: Centralized Billing Tracking
The system SHALL track token consumption per user, per agent, and per workspace using `litellm.success_callback`. Metrics MUST be exposed on `/metrics` for Prometheus scraping.

#### Scenario: Token usage tracked after completion
- **WHEN** an LLM completion request finishes successfully
- **THEN** `prompt_tokens`, `completion_tokens`, `total_tokens`, `model`, `user_id`, `workspace_id` are logged
- **THEN** `agnosticai_llm_tokens_total{model, workspace, user}` counter is incremented

### Requirement: Model Fallback on Provider Failure
If the primary LLM provider returns a 5xx error or rate limit (429), the router SHALL attempt fallback to the next configured provider in the fallback chain.

#### Scenario: Primary provider rate-limited
- **WHEN** OpenAI returns HTTP 429 for a request
- **THEN** litellm automatically retries with the configured fallback model (e.g., `claude-3-5-haiku`)
- **THEN** a `agnosticai_llm_fallback_total{from_model, to_model}` counter is incremented
- **THEN** the user receives a response without visible interruption
