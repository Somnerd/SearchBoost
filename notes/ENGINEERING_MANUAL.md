# SearchBoost Engineering & Cooperation Standards

This document serves as the mandatory protocol for AI agents and collaborators working on the SearchBoost project. It prioritizes stability, respect for existing architecture, and extreme awareness of development overhead.

## ✨ The Showcase Standard (CV-Grade Quality)

This project is not a sandbox; it is a professional showcase and a core component of the creator's professional identity (CV).

- **Gold Standard Logic**: Every fix must be architecturally sound. Avoid "hacks" or temporary patches.
- **Respect for Craftsmanship**: The core logic was built with the creator's "own two hands." Any modifications must respect and preserve the original intent and quality of that work.
- **Production Readiness**: Code must be clean, documented, and resilient enough to handle real-world users and public visibility (e.g., Reddit showcases).

## 🛡️ The 25-Minute Rule (Build Cycle Awareness)

Every code change that triggers a container rebuild (especially Rust/Warden) has a minimum cost of **25 minutes** (10m Review + 10m Build + 5m Testing).

- **NEVER** suggest tiny, iterative code changes that force multiple rebuilds.
- **BATCH** logic updates. Propose the entire system fix (Rust + Python + Config) in one go.
- **VERIFY** logic mentally and with logs before requesting a build.

## 🏗️ Respect the "Working" State

If a component is described as "working fine" or "great even" (e.g., the `sb_worker`), it is considered **Read-Only**.

- **Do not refactor** working code for aesthetic reasons or "cleaner" signatures.
- **Adapt the new code** to the existing working interfaces, not vice versa.
- If a change to a working component is truly necessary for a fix, it must be the **last resort** and explicitly approved.

### 👻 The Ghost in the Machine Clause
If the AI identifies a potential Security Vulnerability or a Critical Race Condition in a "Read-Only" component, it must flag it with a **'CRITICAL WARNING'** prefix but still refrain from editing until the human gives an explicit **'Security Overhaul'** mandate.

## 🤝 The "Handshake" Protocol (Propose Before Edit)

SearchBoost is a distributed system with strict inter-language serialization (Rust vs. Python).

1. **Analyze**: Identify the failure in the handshake (JSON keys, positional arguments, Redis protocol).
2. **Propose**: Detail the exact changes across all affected files in the chat.
3. **Wait**: Do not touch the files until the human partner gives a "Logic OK."
4. **Execute**: Once approved, apply the changes as a single transaction to keep the codebase synced.

## 🕵️ Non-Intrusive Debugging

Before suggesting a code change, use the tools already at your disposal:

- **`docker exec`**: Test theories inside the containers.
- **`redis-cli`**: Inspect the raw state of the queue.
- **Logs**: Use `tracing` (Rust) and `logging` (Python) to pinpoint errors.

## 🔮 The Rule of Three (Verify Thrice)

Every single line change, especially library function calls, must be verified **thrice** before proposal.

1. **Documentation**: Check the exact library version and function signature.
2. **Source Code**: Verify how the variable/function is actually used in the local codebase.
3. **Logic Flow**: Mentally simulate the data flow to ensure there are no side effects or "Handshake" mismatches.
*Speed is irrelevant if it costs a rebuild.*

## 🪵 The Gospel of Logging

Logs are the bread and butter of this project. They are not "optional output"; they are the primary source of truth for the system's state.

- **Traceability**: Every request must be traceable from the Orchestrator through the Warden and into the Worker using the Job ID.
- **Log Levels**: Respect the `--info` flag. Use `DEBUG` for high-frequency internal state and `INFO` for core lifecycle events.
- **The Log Collector**: Before forming any hypothesis, use the `log_collector.sh`. Analysis must start with fresh multi-service logs.

## 🧪 The Test Suite Mandate

Before any new features are added to the system, a robust baseline of automated tests must be established.

- **Test-First Maintenance**: Every bug fixed must be accompanied by a regression test to ensure it never returns.
- **Unit Coverage**: Individual modules (Warden Relay, Worker Logic, Configurator) must have isolated unit tests that run in milliseconds, not minutes.
- **Functional Validation**: The complete "Handshake" (Orchestrator -> Warden -> Redis -> Worker) must be validated by functional suites to ensure cross-language compatibility.
*Feature velocity is secondary to system reliability.*

## ⚖️ Identity & Authority

- **Warden is the Authority**: It handles IDs, timing, and distribution.
- **Worker is the Executor**: It should remain as simple as possible, receiving exactly what it needs to run a task.
- **User Ownership**: The user owns the "Flow." Avoid taking over the project or making decisions that hide system behavior (like hardcoded IDs or silent defaults).

---
*Created on 2026-03-15 by Antigravity (Assistant) as a binding agreement for all future sessions.*
