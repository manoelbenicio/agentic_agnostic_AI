# Tasks: Live Integration Test for Herdr

## Phase 1: Setup & Scaffolding
- [x] Create `tests/test_herdr_live.py`.
- [x] Add `pytest` marker registration for `integration` in `pyproject.toml` or `pytest.ini` so these tests can be filtered out during standard fast runs.
- [x] Add a fixture `live_adapter` in `tests/test_herdr_live.py` that connects to the real `~/.config/herdr/herdr.sock` path based on config.

## Phase 2: Implementation of Test Cases
- [x] Implement `test_live_adapter_agent_list` to verify `result.agents` parsing.
- [x] Implement `test_live_adapter_subscribe_status` to verify event streaming.
- [x] Implement `test_live_adapter_pane_send_and_read` to verify command injection and output capture.

## Phase 3: Execution and Fixes
- [x] Run the tests against the local Herdr 0.7.0 instance.
- [x] Fix any remaining parsing errors or socket timeout issues discovered in `adapter.py` during live execution.
- [x] Document how to run the integration tests in `QA_TESTBOOK_v1.0.0.md`.
