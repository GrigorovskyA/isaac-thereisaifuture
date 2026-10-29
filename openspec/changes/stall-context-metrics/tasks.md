## 1. Implementation

- [x] 1.1 `stall_facts` and `last_room_clear` in the env summary; `STALL_FIELDS` and the header
  upgrade in `episode_metrics.py`; `LiveBackend.oracle_enemy_count()`.
- [x] 1.2 Tests `tests/test_stall_context.py`; docs in `docs/TRAINING_SESSION.md`.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [ ] 2.2 Native session: every stall row of `episodes.csv` has the `stall_*` columns filled and
  the old rows keep empty cells after the one-time header upgrade.

Windows follow-up (2026-10-29): Check1427 includingLua/no skips and strict specs25/25
passed at bc5e985. Authorized no-initialize resume fromt15360 stopped early att16384:
pause_ok0/1, foreground refusal; startup also had a faulted automatic attempt.
All60 old episode/15 train rows preserved; new6 stall/1 death contexts were valid
in the available sample. Task2.2 remains unchecked: full-hour acceptance not reached.
No fix or retry. [Report](../../../reports/2026-10-31-schema8-pause-stall-training.md).
