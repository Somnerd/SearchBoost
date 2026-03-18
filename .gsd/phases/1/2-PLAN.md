---
phase: 1
plan: 2
wave: 2
---

# Plan 1.2: Add Test Suite for Worker Components

## Objective
Add automated tests specifically to verify that `web_search.py` and `ollama_client.py` gracefully handle slow API responses.

## Context
- .gsd/SPEC.md
- `searchboost_tests/`
- `searchboost_service/searchboost_src/web_search.py`
- `searchboost_service/searchboost_src/ollama_client.py`

## Tasks

<task type="auto">
  <name>Create Unit Tests</name>
  <files>searchboost_tests/test_timeouts.py</files>
  <action>
    - Add `pytest` testing for `web_search.py` mocking `httpx.AsyncClient.get` to raise `TimeoutException` and verifying the fallback is triggered.
    - Add test for `ollama_client.py` mocking `ollama.AsyncClient.chat` to sleep for longer than 15 seconds, verifying it triggers `asyncio.TimeoutError` and returns the fallback string.
  </action>
  <verify>pytest searchboost_tests/test_timeouts.py</verify>
  <done>All tests must pass against simulated timeouts without hanging.</done>
</task>

## Success Criteria
- [ ] `searchboost_tests/test_timeouts.py` exists and can run.
- [ ] Tests prove the timeouts work and don't block.
