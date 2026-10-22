# Tasks

## 1. Offline diagnostics

- [x] 1.1 Implement default-off bounded lifecycle records according to design.md; preserve all authorization and wire behavior.
- [x] 1.2 Instrument dispatch before/after, callback entry/exit, approval preserve/drop, close and pre-validation hello facts.
- [x] 1.3 Add production-Lua tests for single restart, additional exit/start, duplicate exit, start-before-exit and disconnect ordering; label simulated sequences explicitly.
- [x] 1.4 Test missing/expired approval and elapsed lease, count/time/byte bounds through reconnect/epoch changes, diagnostic fault/reentrancy isolation and enabled/disabled behavior parity.
- [x] 1.5 Document record fields, diagnostic limits, private capture and closed-game enable/rollback procedure in docs/RESTART_LIFECYCLE_DIAGNOSTICS.md.

## 2. Verification and evidence

- [x] 2.1 Run Windows scripts/Check.ps1 and scripts/OpenSpec.ps1 validate --all --strict; report commands, exit codes and actual counts.
- [x] 2.2 Self-review diff against specifications, with explicit checks for unchanged approval invalidation, expiry, attempts and cleanup.
- [x] 2.3 Record implementation evidence with reports/EVIDENCE_TEMPLATE.md; distinguish candidate offline reproduction from confirmed engine ordering.

## 3. Separately authorized runtime acceptance

- [x] 3.1 After operator normal exit and closed-game preflight, deploy reviewed diagnostics with hashes/backups; predeclare a finite capture and existing authorization limits without approval renewal on reconnect.
- [x] 3.2 Record a natural-death restart and operator handoff/reconnect if it occurs within budget; correlate diagnostic records with the native log. No forced death or additional reset.
- [x] 3.3 Verify disconnect release and operator manual control, preserve private logs, restore default-off build while closed; record exact unresolved questions or blockers.

## Workflow follow-up

- Keep this change unarchived while implementation or required runtime evidence is missing.
- Define any lifecycle behavior fix separately after evidence identifies its trigger.
- Do not assign an external executor or resume monitoring through this plan alone.
