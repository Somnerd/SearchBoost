# Implementation Plan - UI/UX & Context Bug Fixes

This plan addresses the 4 critical bugs identified during manual QA of the Phase 7 production environment.

## User Review Required

> [!IMPORTANT]
> **Context Isolation**: We are modifying the backend semantic search to EXCLUDE the current thread's messages from the "cross-thread" context. This solves the duplication/leakage issue while preserving long-term memory.

## Proposed Changes

### [Backend] Context Leakage Fix

#### [MODIFY] [database.py](../../searchboost_service/searchboost_src/database.py)
Update `search_relevant_history` to accept an `exclude_session_id` parameter. This prevents the LLM from receiving the same messages twice (once in the linear history and once in the semantic context).

#### [MODIFY] [service.py](../../searchboost_service/searchboost_src/service.py)
Pass the current `self.session_id` to the semantic search call.

---

### [Frontend] UI & UX Fixes

#### [MODIFY] [Search.jsx](../../searchboost_ui/src/pages/Search.jsx)
- **Thinking Animation Binding**: Refactor the polling logic to ensure that `pending: false` is set immediately upon receipt of a result, and that the `jobId` mapping is robust against re-renders.
- **Justification / Alignment**: Fix the CSS/Layout to ensure user messages are truly right-aligned. We will use a combination of `align-self` and `flex-container` properties to force the correct bubble placement.
- **Poll State Hygiene**: Ensure that `fetchHistory` (which is called on thread switches) doesn't accidentally wipe out an active polling state for a message in progress (via an intelligent merge of existing and new history).

#### [MODIFY] [index.css](../../searchboost_ui/src/index.css)
Refine the `.chat-bubble-user` and `.chat-bubble-ai` classes to ensure they use proper margins (`margin-left: auto` for user) to guarantee alignment even if `align-self` is constrained by flex settings.

## Open Questions

- **Thinking Animation**: Would you prefer the thinking animation to stay visible even if you switch back and forth between threads (requires saving "pending" state to local storage or DB)? Current behavior only shows it if you stay on the thread where the search started.

## Verification Plan

### Automated Tests
- Restart backend services and verify logs show "Context filtered: excluding current session".

### Manual Verification
1.  **Alignment**: Confirm user bubbles are pinned to the right edge.
2.  **Context**: Ask a question that appeared in a *different* thread and confirm it works. Then ask about the *current* thread and check logs to ensure no duplication.
3.  **Animation**: Verify the "Researching..." dot-pulse disappears exactly when the text result replaces it.
4.  **Multi-message**: Send two messages in quick succession and verify only the second one shows the thinking animation once the first completes.
