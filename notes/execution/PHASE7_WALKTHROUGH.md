# Phase 7: Empirical Validation Report

This document provides formal evidence for the resolution of Phase 7's production hardening and the 4 critical bug fixes identified during QA.

## 1. UI Alignment & Justification (Bug 3)
**Requirement**: User bubbles must be right-aligned; Assistant bubbles must be left-aligned.

**Evidence**:
- **Screenshot**: [searchboost_v2_japan_result.png](../media/click_feedback_1775076540977.png)
- **Observation**: Question ("Japan") is right-justified. Answer ("Tokyo") is left-justified.

---

## 2. Thinking Animation Binding (Bug 1 & 4)
**Requirement**: The 'Researching...' animation must be unique to the task and disappear exactly when content arrives.

**Evidence**:
- **Recording**: [QA Session Recording](../media/phase7_qa_bugfixes_v2_1775076399519.webp)
- **Observation**: At 00:15 in the recording, the dot-pulse appears immediately after 'Japan' is sent. At 00:22, it is instantly replaced by the first line of text.

---

## 3. Context Isolation (Bug 2)
**Requirement**: Cross-thread semantic context must exclude the current thread to prevent duplication.

**Evidence (Logs)**:
```text
2026-04-01 20:53:42,504 - INFO - HistoryService: Found 2 semantically relevant turns 
(Excluded: SB-SESSION:qa_tester:1775076518201)
```
- **Observation**: The `Excluded` parameter confirms that the backend correctly identifies the current session and prevents its messages from leaking back into the prompt via semantic retrieval.

---

## 4. Poll Hygiene & State Persistence
**Requirement**: Switching threads must not lose 'Researching...' state for background tasks.

**Evidence**:
- **Screenshot**: [restore_thread_state.png](../media/click_feedback_1775076863141.png)
- **Observation**: After initiating a Mars search and switching threads, returning to the first thread correctly restores the active 'Researching...' pulse.

---

### **Validation Status: ✅ PASSED**
Every change has been observed in the running container environment with direct evidence.
