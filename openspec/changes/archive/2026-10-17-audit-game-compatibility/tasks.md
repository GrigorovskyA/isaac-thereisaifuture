# Tasks

## 1. Local inventory and isolation

- [x] 1.1 Deliver sanitized Steam/game/runtime/mod inventory in COMPATIBILITY_AUDIT, cross-checked against local manifests, files, configuration, and logs.
- [x] 1.2 Deliver actual save/Cloud locations and isolation/restoration options in the audit, including shared mod data and runtime synchronization risks.

## 2. Source audit and implementation decision

- [x] 2.1 Deliver pinned commits, licenses, transport/blocking and dependency findings for SocketBridge and alternatives, checked against source.
- [x] 2.2 Deliver required-capability matrix with source references, unknown runtime results, and exact future probe scenarios.
- [x] 2.3 Deliver one bridge recommendation and concrete bridge-handshake-and-observation handoff with explicit authorization gates.

## 3. Integrated audit verification

- [x] 3.1 Run Check.ps1 and change strict validation; record commands, exits, acceptance mapping and a separate OpenSpec self-review in the evidence report.
- [x] 3.2 Update STATUS, roadmap and setup/source pointers; review the complete diff for consistency, English language and private data.

## Workflow follow-up

- Archive and sync only after all seven audit tasks and declared acceptance criteria pass.
- Runtime bridge, action, reset, isolation-write and RL tests are outside this audit;
  record them as blocked/not_run, never as passed. They remain later milestone gates.
- Commit and push only project artifacts after final validation; exclude all local
  saves, raw/private logs, credentials, downloaded source and machine identities.
