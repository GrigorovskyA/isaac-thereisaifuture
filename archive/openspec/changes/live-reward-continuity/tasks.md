## 1. Implementation
- [x] 1.1 Remove absence-derived damage/kills and add bounded HP-floor continuity with gap/reset/context handling.
- [x] 1.2 Add backward-readable reward contracts and reject incompatible training resume before environment creation.
- [x] 1.3 Add behavioral regressions for repeated healing/reset,gaps,overflow,context,max-HP mutation,bounds and compatibility.

## 2. Verification
- [x] 2.1 Run targeted tests and full Windows quality gates with the bounded Luna worker; primary verifies logs and hashes.
- [x] 2.2 Perform separate self-review and OpenSpec verification; update evidence,STATUS and roadmap.
- [x] 2.3 Record a newly bounded installed-game continuity check across a software boundary; keep pending if not run. No exact kill-channel acceptance is claimed.
