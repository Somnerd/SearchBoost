# Manual QA Test Plan
**Target Environment:** `dev-web-ui` (Phase 5 & Semantic Caching)


## Test 1: UI Session Multi-Thread Isolation
**Method:** Browser UI (`http://${SB_INSTANCE_IP}`)
**Objective:** Confirm that the React component spawns clear isolated `thread_id` records in PostgreSQL and visually renders them simultaneously.
**Steps:**
1. Login to the application.
2. Search "test query 1". Verify sidebar parses session ID.
3. Click '+ New Chat'.
4. Search "test query 2". Verify second session appears independent of the first main view.
**Expected:** The UI sidebar must list two distinct session IDs. Both threads must persist independent conversation states upon page refreshes.


## Test 2: PII-Safe Semantic Caching (Hard Gate)
**Method:** Terminal (`curl` / `redis-cli`)
**Objective:** Confirm that sensitive inputs (e.g. Credit Cards) are actively rejected by the `PIIDetector` and NEVER written to the Redis cache.
**Steps:**
1. Clear existing semantic cache keys (`redis-cli KEYS "semantic_cache:*" | xargs redis-cli DEL`).
> [!NOTE]
> Pattern-based clearing is safer than `FLUSHALL` in shared environments and prevents accidental data loss for other services.
2. Enqueue a search containing fake PII: "My credit card is 4111-1111-1111-1111, when does the world series start in 2024?".
3. Wait for the pipeline to complete.
4. Check Redis keys using `redis-cli KEYS "semantic_cache:*"`.
**Expected:** The `semantic_cache` MUST NOT contain any keys corresponding to the PII-laden query.


## Test 3: Post-Optimization Cache Check
**Method:** Terminal (`curl` / `redis-cli`)
**Objective:** Confirm that two different inputs requesting identically structured semantic outcomes match via the underlying optimized string, avoiding multiple external searches.
**Steps:**
1. Clear existing semantic cache keys (`redis-cli KEYS "semantic_cache:*" | xargs redis-cli DEL`).
2. Enqueue Request A: "can you tell me who the current president of france is right now"
3.  Wait for LLM optimization and response. Check Redis for keys.
4. Enqueue Request B: "who is president france"
**Expected:** The system should instantly flag a post-optimization CACHE HIT on the second query. Verify the hit via Warden logs (`Checking semantic cache... HIT`).


## Test 4: Database History Persistence (Persistence Tier)
**Method:** Terminal (`psql`)
**Objective:** Confirm that threads and individual user messages are correctly mapped to the PostgreSQL `history` table with proper ownership.
**Steps:**
1. Identify the current user's session identifier (e.g., `SB-SESSION:username:default`).
2. Run SQL query: `SELECT * FROM history WHERE session_id = 'YOUR_SESSION_ID';`.
3. Verify that the `query` and `response` columns contain the expected text.
**Expected:** The database should contain one row for each search interaction. `username` and `session_id` must match the active UI session.
