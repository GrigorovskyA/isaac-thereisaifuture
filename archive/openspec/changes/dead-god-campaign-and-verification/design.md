## Context

`eligibility.py` and `progression.py` provide the gate, ledger and goal selection. Nothing
composes them into a campaign or decides when the target counts.

## Decisions

- **Injection**: `run_once(goal) -> RunReport`, eligibility evidence supplier, clock and timestamp
  are injected, so the loop is deterministic offline and independent of the full-run module.
- **Fail closed**: eligibility is evaluated before and after each run; any denial stops the
  campaign (`ineligible`) and post-run denial discards that run's evidence.
- **Evidence**: only `evidence_source == "observed_in_game"` is ledgered; goals not in the graph
  stop the campaign (`invalid_report`).
- **Resume**: state file (JSON, atomic replace) keeps runs, audits and denials. Budgets count total
  runs across resumes. A state left `running` is counted as an interrupted run and never replayed;
  a corrupt state raises `CampaignStateError` instead of restarting.
- **Stop reasons**: `target_observed`, `max_runs`, `max_wall_seconds`, `ineligible`, `run_fault`,
  `invalid_report`, `ledger_invalid`.
- **Verification**: `verified` requires a valid ledger, observed target evidence, and for every
  observed ledger event a run with two allowed audits, and no interrupted run. `blocked` means
  verification was impossible (bad ledger or state); otherwise `unverified`. Autonomous and
  user-assisted runs are counted separately.
- This does not prove the game recognizes Dead God; real restart reconciliation stays blocked.
