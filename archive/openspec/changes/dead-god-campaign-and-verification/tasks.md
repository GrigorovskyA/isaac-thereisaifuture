## 1. Implementation (offline)

- [x] 1.1 Add `campaign.py` (controller, state file, budgets, stop reasons, verification).
- [x] 1.2 Write tests/test_campaign.py covering each refusal path.

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate dead-god-campaign-and-verification --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Reverify the online/mod Dead God requirement on the target build and design an eligible path.
- [ ] 3.2 Wire the real full-run `run_once` and eligibility evidence from the bridge.
- [ ] 3.3 Reconcile Dead God on file 2 after normal restart; evidence report; only then archive.
