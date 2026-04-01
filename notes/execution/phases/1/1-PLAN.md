---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Fix Blocking I/O and Enforce Timeouts

## Objective

Migrate synchronous blocking `requests` to asynchronous `httpx` in `web_search.py`, and implement explicit strict timeouts in both the search and AI handling layers so the worker stops locking up.

## Context

- .gsd/SPEC.md
- .gsd/phases/1/RESEARCH.md
- `searchboost_service/searchboost_src/web_search.py`
- `searchboost_service/searchboost_src/ollama_client.py`

## Tasks

<task type="auto">
  <name>Migrate web_search.py to httpx</name>
  <files>searchboost_service/searchboost_src/web_search.py</files>
  <action>
    - Replace `requests.get()` with `httpx.AsyncClient().get()` using a 10-second timeout.
    - Ensure `async with httpx.AsyncClient() as client:` is used.
    - Handle `httpx.TimeoutException` or `httpx.RequestError` gracefully by returning a fallback response string.
  </action>
  <verify>python3 -c "import httpx; print('httpx available')"</verify>
  <done>Synchronous requests import is removed and the function performs fully async HTTP yielding.</done>
</task>

<task type="auto">
  <name>Enforce timeout in ollama_client.py</name>
  <files>searchboost_service/searchboost_src/ollama_client.py</files>
  <action>
    - Wrap the `self.client.chat(...)` invocation in an `asyncio.wait_for(task, timeout=15.0)`.
    - Catch `asyncio.TimeoutError` and return a standard fallback response from the LLM warning about the timeout.
  </action>
  <verify>cat searchboost_service/searchboost_src/ollama_client.py | grep wait_for</verify>
  <done>If `client.chat` takes longer than 15 seconds, it aborts gracefully instead of hanging for 70 seconds.</done>
</task>

## Success Criteria

- [ ] No synchronous network requests exist in `web_search.py`.
- [ ] Ollama fails fast if it takes longer than 15 seconds.
