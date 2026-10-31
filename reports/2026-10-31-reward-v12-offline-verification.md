# Reward v12 and session-start fallback: offline verification

October31,2026. Changes: session-start-new-run-fallback and
 door-pull-and-short-stall-reward-v12. This is self-review, not independent review.
User-requested publication and native attempt are distinct from native acceptance.

## Verification scorecard

| Dimension | Session entry | Reward v12 |
|---|---|---|
| Completeness | 3/4 tasks; native2.2 pending | 8/11 tasks; native2.2/2.3/2.4 pending |
| Correctness | Added entry requirement mapped to enter_file2/session_runner and tests; native scenario not yet run | Five added requirements mapped to coefficients/config/live/training and test_reward_v12; native performance not yet measured |
| Coherence | Existing bounded fresh-log/menu key ownership pattern preserved; design adherence not verified (no design artifact supplied) | Design values, contract mismatch refusal, persistence and old-version compatibility match implementation |

Incomplete native tasks prevent full acceptance/archive. No missing implementation
was found in reviewed scope; one previously uncovered contradictory-log scenario
now has a regression test that confirms no entry key is sent. No archive requested.
The session-entry change has no design.md; no design adherence is asserted for it.

## Checks

Full scripts/Check.ps1 passed:1569 tests including isolated Lua5.3, no skips;
ruff lint/format,mypy,pip check clean. One existing synthetic All-NaN warning.
Strict scripts/OpenSpec.ps1 validate --all --strict passed30/30, exit0.
The first preliminary run skipped optional Lua and encountered an existing shared
TEMP cleanup access denial; the authoritative rerun used process-local TEMP/TMP and
test-only lupa2.6 in reports/local/reward-v12-schema9-20261031/lua-runtime with the
installed JSON decoder. Project dependencies and global PATH were not changed.
Authoritative log: reports/local/reward-v12-schema9-20261031/check-full.log.

Tests cover exact v12 value changes, doubled potential payments, required/forbidden
stall sections, invalid stall limits, mismatch refusal in live/config and death/stall
cost order. Current-schema expectations were updated while historic v8/v9 ledger
limits remain40s. Session tests cover loaded Continue, verified absence from all
three selected slots, missing evidence and contradictory evidence, plus existing
bounded focus/ownership/wrong-slot protections.
Contract1a6d8146f5e89b7bdad14fe21d3afa9cc1f5c4192b8e5f24cefb6bbab0e0c8d8
was computed from the validated current config. The manifest reward_contract label
remains pure-v11 by design; reward_version12/hash distinguish the new lineage.
Lua is unchanged; no native behavior is inferred from synthetic tests.

## Native continuation

[Finite plan](2026-10-31-reward-v12-schema9-native-plan.md): preserve v11t253952,
verify deployed hashes without redeployment, initialize once,18-minute passive
audit, first automatic8-hour rollover evidence and50k/150k/300k comparisons.
The target stops at first saved>=300k under a30-hour ceiling, with fault stop/no
manual retry. Native pending tasks stay open until exact evidence exists.
