# Schema 7 pure-v9 one-hour qualification

## Outcome

Passed the measured native qualification checks for the user-authorized conditional
continuation. This is self-review, not full OpenSpec task 2.2 acceptance: no boss was
cleared, so the positive native +20 boss case remains unverified. Task 2.3 stays open.
No code, configuration or mod was changed during qualification.

## Identity and execution

- Windows/Steam, file 2; source revision d789c5d, launch documentation a8f7b6d.
- Observation 7: 3863 inputs; action 2; reward pure-v9; seed 1; ent_coef 0.005,
  gamma 0.998, stall limit 40 seconds.
- Contract: `3cb9d928e397ec26587bb72d89864ecd1dae04094404c36fb60fa282a9749310`.
- One fresh initialization, October 28 17:33:40 UTC to 18:33:45 UTC
  (18:33 to 19:33 CET). The independent one-hour timer requested the stop.
- Session: `session-20261028-183341-0001`; final checkpoint
  `3cb9d928-s1-t13824`, saved 18:33:42 UTC / 19:33:42 CET.
- Learner exit 0, fault null, cleanup_errors empty. Live checks after the hour found
  no Isaac, learner, forever supervisor or hour owner, no listener on port 9528,
  and no owned control approval. stop.forever was present.
- Prior schema 6 t13824 remains under `runs/pure-v4-reward-v9-schema6` with its stop
  marker. It was not resumed. Reward v8 is preserved separately.
- Windows gate: 1325 tests including Lua, no skips; strict OpenSpec 22/22;
  synthetic CPU smoke: 3863 inputs. These offline checks do not establish gameplay quality.
- Lua was not redeployed; preflight source/deployed hashes matched.

## Native checks

| Check | Evidence | Result |
|---|---|---|
| Origin-relative geometry | 13,148 shape-1 samples; 49 outside 13x7 (0.373%) | Passed |
| Doorway exception | All 49 outside samples within 21.451 px of a listed door | Passed |
| Visited bits and origin | Every audited current-cell bit present; zero origin disagreements | Passed |
| Wire size and doors | 69,194 validated snapshots, maximum 12,170 bytes; up to 6 doors | Passed |
| Validation/audit errors | No decode or audit errors | Passed |
| Door potential | Independently recomputed all 13,824 steps; zero potential mismatches | Passed |
| PBRS and episode sums | gamma * Phi_after - Phi_before matches; episode sums match CSV | Passed |
| Continuity/terminal | Zero potential continuity errors; all 67 terminal potentials zero | Passed |
| Standing drift | 262 comparable near-still steps, zero excess beyond discount and bounded subpixel jitter | Passed |
| Invalid boss bonus | No bonus outside a boss room | Passed |
| Positive boss bonus | No boss-clear events encountered | Not covered |

Cell indices use floor((x-60)/40), floor((y-140)/40), with 26x14 storage and a
13x7 shape-1 interior. Outside examples include (56.652,286.577), (583.546,281.060)
and (329.288,421.426), all at doorways. There is no observed schema-6 origin mismatch.

Door potential was recomputed only for clear/no-enemy rooms with open unexplored
doors, using coefficient 2 and the shape bounding-box diagonal; terminal potential
is zero. All episode totals stay within the potential bound plus discount residual;
observed col_door_shaping ranges from 0.203392 to 1.261613.
There are 67 completed episodes, totaling 13,625 episode steps. All 67 have a
nonzero door term; 61 have no explicit rooms_cleared event because their starting
room was already clear. This is an eligible clear-room potential, not proof of a
combat clear. The audit includes additional in-flight steps beyond completed rows.
No systematic standing reward beyond the specified discount residual was found.

## Conditional continuation and limits

The qualified parent is `3cb9d928-s1-t13824`. The prepared continuation may resume
this exact checkpoint without initialization, with unchanged frozen inputs and
an absolute stop at October 30 08:00 UTC / 09:00 CET. Five consecutive faults and
the 20,480,000,000-byte disk cap still stop execution. No new evaluation is authorized.
A final report will summarize approximately 30k-step windows, all reward components,
sessions, faults and actual shutdown. This report does not claim better native play.

Local evidence (excluded from Git): `reports/local/pure-v9-schema7-20261028/`
contains result.json, assessment.json, independent-review.json and
qualification-review.json; raw audit and session evidence are under `runs/pure-v4/`.

Historical comparison: [schema 6 qualification](2026-10-29-pure-v9-training.md).
