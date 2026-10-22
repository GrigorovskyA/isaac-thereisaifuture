# Tasks

## 1. Protocol and Python

- [x] 1.1 Implement strict typed messages, bounded framing and ordering; verify malformed/version/identity cases with offline tests and document protocol examples.
- [x] 1.2 Implement context-managed loopback consumer and observe CLI; verify simulated handshake, fragmentation, timeouts, reconnect and interruption cleanup.

## 2. Lua observer

- [x] 2.1 Implement nonblocking observation-only Lua adapter; verify partial I/O, absent/slow/malformed peer and state lifecycle in a labeled Lua stub harness.
- [x] 2.2 Verify API prerequisites and document field semantics, unknown runtime capabilities, exact artifact hashes/install/activation and rollback steps.

## 3. Integrated offline verification

- [x] 3.1 Run targeted tests, Check.ps1, OpenSpec strict validation and separate self-review; record evidence and update STATUS/roadmap without claiming integration.

## 4. Authorized real-game verification

- [x] 4.1 Verify approved profile and specific deployment authorization; install observer and prove actual handshake, advancing frames and manually correlated position/health/room.
- [x] 4.2 Complete ten-minute observation soak and disconnect/reconnect/Python-shutdown responsiveness check with real evidence and cleanup.

## 5. Terminal observation launcher

- [x] 5.1 Implement bounded script launch, listener-before-game ordering, artifact/running-game guards, terminal logs and owned-resource cleanup; run offline checks.
- [x] 5.2 Verify the script's real closed-game launch and actual handshake under the existing specific read-only authorization, with file-2 selection recorded separately.
- [x] 5.3 Record the Dead God target, progression dependencies and automatic slot-selection unknowns in the roadmap and handoff; verify OpenSpec and self-review.
- [x] 5.4 Add bounded reconnection after observed user death/restart; verify fresh identity, shared sample/deadline budgets, retry exhaustion and fail-fast protocol errors offline.
- [x] 5.5 Verify the updated launcher's automatic reconnection with the actual game; distinguish it from the separate observe CLI probe.

## Workflow follow-up actions

- Commit and push completed project work, excluding local/private data.
- Archive only when all acceptance tasks pass. If runtime is blocked, retain the
  active change and unchecked tasks 4.1–4.2. Stop before bridge-safe-actions.
