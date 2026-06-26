# Proposal: Live Integration Test for Herdr (HM-FIX-05)

## 1. What
Create a live integration test (`test_herdr_live.py`) that physically connects HerdMaster's `HerdrAdapter` to a real running Herdr 0.7.0 socket. The test will perform basic CRUD and subscription verifications against the official socket API (`agent.list`, `events.subscribe`, `agent.send`).

## 2. Why
As diagnosed, the existing test suite has a "blind spot". It uses a mocked `HerdrAdapter` built against an obsolete specification (`RESEARCH_Herdr_Capabilities.md`). While the domain logic tests (Watchdog timeouts, DB queues) are robust, they don't guarantee integration with Herdr 0.7.0 works. This live test will prove that INC-005 is fully resolved and that HerdMaster can reliably orchestrate real agents.

## 3. Success Criteria
- [ ] A dedicated `pytest` integration test exists and is marked as such (`@pytest.mark.integration`).
- [ ] The test connects to `~/.config/herdr/herdr.sock` (or config path).
- [ ] The test issues an `agent.list` RPC call and successfully parses the JSON envelope (`result.agents[]`).
- [ ] The test subscribes to `events.subscribe` and correctly receives `pane.agent_status_changed` events.
- [ ] The test runs without breaking existing mocked unit tests.

## 4. Non-goals
- Full E2E logic (simulating tasks and planning). This change focuses purely on proving the adapter's raw connection to Herdr works.
- Load testing or chaos engineering (these are Phase 2/3 goals).
