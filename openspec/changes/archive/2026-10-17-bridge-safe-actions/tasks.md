# Tasks

## 1. Prerequisites and contract

- [x] 1.1 Document current isolation/slot blockers, native API evidence, approval/write-set/restoration requirements and protocol; verify against existing evidence without live control.
- [x] 1.2 Deliver proposal/design/delta specs and validate bridge-safe-actions --strict (initial warnings must be corrected before delivery).
- [x] 1.3 Resolve verified isolated profile OR recorded user-approved ordinary-profile test exception, actual instance/operator-confirmed active-slot identity and specific runtime authorization; verify the local authorization record before any live action.

## 2. Offline implementation

- [x] 2.1 Implement gated Lua native input/command state machine, expiry and cleanup, preserving default observation/restart; verify behavioral Lua tests including stale commands and reconnects.
- [x] 2.2 Implement strict Python command/ack models and bounded attach-only client; verify simulated socket transactions, failures and cleanup, and document API.

- [x] 2.3 Implement expiring private local approval, 120-second per-mod-load authority, native tear/release diagnostics and a finite attach-only sequence probe; verify offline expiry/exception/evidence tests and document user authorization.

## 3. Verification and delivery

- [x] 3.1 Run Check.ps1 with all Lua tests enabled and OpenSpec strict validation; perform separate self-review and record results in the evidence template, STATUS and ROADMAP.
- [x] 3.2 After task 1.3, deploy reviewed hashes with game closed and verify 50 controlled sequences with actual movement/shooting and measured release after disconnect/Python failure; retain identity-bound evidence.

## Workflow follow-up

- Keep active and unarchived until every declared acceptance task passes.
- Commit and push reviewed project changes, excluding private logs/saves/backups.
