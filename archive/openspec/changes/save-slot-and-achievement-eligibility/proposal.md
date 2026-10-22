## Why

Roadmap item 19: autonomous progression toward Dead God must happen only on save file 2 with
achievements enabled and no console, debug, edited/imported save or achievement-blocking mod.
Unknown identity must block control rather than silently use another file.

## What Changes

- Add `eligibility.py`: `EligibilityEvidence`, `EligibilityDecision`, `EligibilityError`,
  `evaluate`, `require_eligible`, `audit_record`.

## Scope and non-goals

- This is an **offline contract only**. The real bridge does not yet expose slot identity or
  achievement fields (blocked); `EligibilityEvidence` is the contract the bridge must fill.
- Out of scope: slot selection API, save handling, Steam/Cloud isolation, unlock evidence after
  restart, progression ledger (item 20).
- Risk: field semantics for the installed build are unverified; a separate slot does not establish
  settings, Cloud or Steam achievement isolation.
- Must NOT be archived until real evidence exists (bridge-observed slot, legitimate unlock kept after
  restart on file 2, untouched files unchanged).
