## Why

Roadmap item 21: the final goal (Dead God on save file 2, earned through gameplay) needs a
bounded, resumable campaign loop and a verification rule that cannot be satisfied by edited,
imported, console-assisted or merely claimed evidence.

## What Changes

- Add `campaign.py`: `CampaignController`, `RunReport`, `CampaignLimits`, `verify_campaign`.
- Each run is gated by eligibility (before and after), goal chosen by `select_next_goal`, evidence
  appended to the ledger only when reported as `observed_in_game`.
- Budgets (`max_runs`, `max_wall_seconds`), explicit stop reasons and a persistent state file.

## Scope and non-goals

- Offline contract only. `run_once` is injected; no game launch, no real bridge, no saves touched.
- Not resolved: whether a fully autonomous mod-based agent can meet the online-achievement
  requirement for new Dead God files (see docs/PROGRESSION_GOAL.md). No promise is made.
- This change MUST NOT be archived until real file-2 evidence exists.

## Risks

- Eligibility fields are not yet exposed by the real bridge (blocked); unknown means denied.

## Acceptance criteria

- Offline: every refusal path (ineligible, evidence lost mid-run, non-observed evidence, unknown
  goal, fault, budgets, corrupt state, tampered ledger, missing audits) has a test.
- Pending real game: the game recognizes Dead God on file 2 and it persists after normal restart.

## Impact

New module `campaign.py`; no change to existing modules or wire protocol.
