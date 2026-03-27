# Project Specification: Phase 5 - Concurrent Chat Sessions

## Goal
Implement a ChatGPT-like concurrent session history layout where users can navigate between previous chat threads seamlessly. 

## Requirements
1. **Thread Identification**
   - The React UI must generate unique session IDs (`thread_id`) when a conversation is started.
2. **Backend Persistence & API**
   - The Node.js API must decouple absolute `SB-SESSION-{username}` history retrieval and update queries to track isolated unique `thread_id` records appended onto the user scope.
   - Example endpoints: `GET /search/sessions/` and `GET /search/history/:thread_id`.
3. **Sidebar UI**
   - The React UI must render a toggleable sidebar dynamically loading past historical thread navigation instances.
   - Hitting "Start New Conversation" produces a blank view referencing a new uninitialized `thread_id`.
