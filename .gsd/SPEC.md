# Project Specification: Fix Worker Hangs (FINALIZED)

## Goal
Resolve the bug where the Python arq worker hangs indefinitely when handling jobs that require `web_search.py` and `ollama_client.py`.

## Requirements
1. `web_search.py` must use non-blocking `httpx` instead of blocking `requests`.
2. `ollama_client.py` and `web_search.py` must have explicit `asyncio.wait_for` timeouts so they fail gracefully instead of taking 70+ seconds.
3. Relevant unit tests must be added to `searchboost_tests/` to verify these timeout limits function correctly.
