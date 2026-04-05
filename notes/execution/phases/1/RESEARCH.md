---
phase: 1
level: 3
researched_at: 2026-03-18
---

# Phase 1 Research: Debugging Worker Hangs

## Questions Investigated

1. **Why does the Python worker fail to process jobs correctly from the Rust Warden? (The Enqueue bug)**
2. **Why does the worker hang and timeout? Is it Ollama, SearXNG, or something else? (The timeout bug)**
3. **How can we maximize logging and test these components robustly?**

## Findings

### Serialization Mismatch (arq vs serde_pickle)

The Rust Warden uses `arq` to queue jobs. The standard `arq` job structure is a pickled tuple: `(job_try, function_name, args, kwargs, enqueue_time)`.
Currently, `searchboost_warden/src/relay.rs` constructs a `serde_json::json!({...})` dictionary object mapping and pickles it. When the Python `arq` worker attempts to unpickle this, it gets a Python `dict`. Python `arq` expects a tuple and attempts to unpack it. This causes severe runtime exceptions on the worker side, rendering the job dead on arrival.
**Recommendation:** Change the job data in `relay.rs` to an explicit Rust tuple `(1, "Worker.run_task", (payload.query, payload.options), {}, enqueue_time_ms)` to ensure it matches `arq`s unpack logic perfectly.

### The Asynchronous Blocking Bug (SearXNG / WebSearch)

Inside `searchboost_service/searchboost_src/web_search.py`, there is an `async def searxng_search(self):` function. However, instead of using an async HTTP client, it utilizes the synchronous `requests.get(..., timeout=10)` library.
When the `arq` worker executes this code, the synchronous `requests` call completely **blocks the main asyncio event loop**. This means the worker literally hangs and cannot process heartbeats, track timeouts, or process other concurrent tasks while waiting for SearXNG.
**Recommendation:** Refactor `web_search.py` to use `httpx.AsyncClient()` to make non-blocking HTTP requests.

### Unbounded AI Model Timeouts (Ollama)

In `searchboost_service/searchboost_src/ollama_client.py`, the `ollama.AsyncClient` makes a `.chat()` call without any explicitly configurable timeout restriction. If the local Ollama daemon stalls or the model is excessively slow, the task hangs indefinitely without failing over or aborting.
**Recommendation:** Introduce `asyncio.wait_for` wrappers or utilize `httpx` timeouts on the `AsyncClient` instantiation.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Fix Serialization | Convert `serde_json` object to a Rust tuple | Will match exactly what Python `arq` expects |
| Fix Blocking I/O | Migrate `requests` to `httpx` | Prevents event-loop blockage |
| Impose Timeouts | Wrap Ollama and SearXNG with explicit boundaries | Ensures tasks fail fast rather than stalling queue |

## Patterns to Follow

- Never use synchronous I/O operations (like `requests` or `time.sleep`) inside an `async` Python function.
- Always use Rust tuples when interfacing with Python `pickle` tuples.
- Ensure thorough test coverage utilizing mock endpoints for SearXNG and Ollama.

## Ready for Planning

- [x] Questions answered
- [x] Approach selected
- [x] Dependencies identified
