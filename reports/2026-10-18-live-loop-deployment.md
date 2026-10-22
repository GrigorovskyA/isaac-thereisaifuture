# Evidence: live-training-loop closed-game deployment

- Date/time and timezone: 2026-10-18, approximately 15:27 CEST.
- Git revision and dirty status: 941c79b; unrelated untracked errors.txt preserved.
- Scope: task 5.2, source observer 0.5.0-dev deployment; no runtime acceptance.
- Game: existing Repentance+ installation; not launched or attached in this operation.
- Configuration: existing Python 3.12.14 environment and pinned dependencies.
- Planned scenario: operator-selected ordinary profile, file 2; random policy,
  seed 18, at most 2000 steps / 6 minutes, zero tolerated infrastructure faults.
  Private approval expires after 15 minutes and allows at most 3 natural-death
  restart attempts. No forced death, reset, save change or initial run start.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Closed game | Process guard before backup and each file copy | 0 | passed | No isaac-ng process |
| Prior installation | SHA256 readback against recorded 0.4.5-dev files | 0 | passed | Both prior hashes match |
| Backup | Copy two installed files and any existing approval to reports/local | 0 | passed | Private timestamped backup; excluded from Git |
| Deployment | Copy only main.lua and metadata.xml; compare source/installed SHA256 | 0 | passed | Hashes below |
| Preflight | `.venv/Scripts/python.exe -m isaac_threrisaifuture.launcher --preflight-only` | 0 | passed | No launch; installed/source hashes match |
| Private approval | write_training_approval, hours=0.25, max_restarts=3 | 0 | passed | Written locally; intended slot explicitly awaits current manual confirmation |
| Windows gate | `./scripts/Check.ps1` | 0 | passed | 1224 tests, zero skips; Ruff, format, mypy, pip and strict OpenSpec 25/25 |
| Live handshake and oracle | Operator readiness required | — | not_run | Task 5.3 remains open |
| Random integration and checkpoint | Real game not attached | — | not_run | Tasks 5.4 and 5.5 remain open |

Installed/source SHA256:

- main.lua: f49ebe390aeb0ad96a0018dedce00978cf8beafdc5f0112eb8d471514c8442d5
- metadata.xml: 00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997

## Real game

The user authorized proceeding with the staged deployment and bounded check.
Separate save-file selection is still manual and is not isolation or automatic
attestation. No listener, action, restart, launch or training was started here.
Approval text explicitly requires current manual file-2 confirmation before attach.
The first approval-writing attempt exceeded the evidence field's 128-character
limit and failed before writing; shorter accurate text passed validation.

## RL evaluation

Not run. Random integration is not evidence of learning. A later short training
check must have a separate explicit budget and follow successful integration.

## Limitations and continuation

Only deployment task 5.2 is accepted. Confirm the operator has manually launched
with --luadebug and selected file 2 in a playable room before connecting.
If approval expires while waiting, do not silently renew it or claim runtime success.
Stop on protocol errors or unexpected lifecycle changes, release input, retain
private logs locally and report observed results. No archive.

## Readiness attempt: expired approval

At the operator's next readiness confirmation, process 37144 was running, but
approval readback showed -2084 seconds remaining. The game had started after
approval expiry. No listener, handshake, action, restart or training was started.
Task 5.3 remains blocked pending operator normal exit, explicit bounded approval
refresh while closed, manual relaunch and fresh file-2 confirmation. Do not renew
this approval silently or write mod files during a live run.

## Operator-directed approval refresh

The operator confirmed normal exit and requested continuation. The process guard
confirmed Isaac absent, both installed/source hashes matched and launcher
preflight passed (exit 0). A deliberate replacement approval was written with
900 seconds remaining and max_restarts=3; expiry is 2026-10-18T16:32:47+02:00.
No game launch or connection occurred. Fresh manual file-2 readiness remains
required before the planned 2000-step / six-minute random check.
