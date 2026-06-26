# Design: Live Integration Test for Herdr

## Architecture
The new test file `test_herdr_live.py` will live under `tests/integration/` or directly inside `tests/` marked with `@pytest.mark.integration`. 
We will use the existing `HerdrAdapter` implementation (`src/herdmaster/herdr/adapter.py`) to connect to a local Herdr instance.

### Prerequisites for the test
- Herdr 0.7.0 must be running locally.
- A socket must exist at `~/.config/herdr/herdr.sock`.
- We will require a `test_config.toml` that points to this socket.

### Test Cases
1. `test_live_adapter_agent_list`:
   - Setup: Read configuration and instantiate `HerdrAdapter`.
   - Action: `await adapter.agent_list()`.
   - Assertion: Should return a list of `HerdrAgent` objects, verifying the parser correctly interprets the `result.agents` array from Herdr 0.7.0.

2. `test_live_adapter_subscribe_status`:
   - Setup: Instantiate `HerdrAdapter` and create an async queue or callback mock.
   - Action: `adapter.subscribe_status(callback)`.
   - Action 2: Trigger a pane state change (e.g. by dispatching a dummy command via `adapter.pane_send`).
   - Assertion: The callback receives a correctly parsed `pane.agent_status_changed` event within a timeout.

3. `test_live_adapter_pane_send_and_read`:
   - Setup: Get an active `pane_id` from `agent_list`.
   - Action: `await adapter.pane_send(pane_id, "echo hello")`.
   - Action: `await adapter.pane_read(pane_id)`.
   - Assertion: The output contains "echo hello" or the execution result.

## Risks & Mitigations
- **Risk:** Tests hang forever if Herdr is down.
  **Mitigation:** Add strict timeouts (`asyncio.wait_for`) around socket operations in tests.
- **Risk:** Tests interfere with real agents in `w4`.
  **Mitigation:** The tests should only use harmless commands (`echo`, or non-destructive read operations) or require a dedicated test workspace if possible. For now, read-only and `echo` are safe.
