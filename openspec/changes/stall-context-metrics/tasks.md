## 1. Implementation

- [x] 1.1 `stall_facts` and `last_room_clear` in the env summary; `STALL_FIELDS` and the header
  upgrade in `episode_metrics.py`; `LiveBackend.oracle_enemy_count()`.
- [x] 1.2 Tests `tests/test_stall_context.py`; docs in `docs/TRAINING_SESSION.md`.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [ ] 2.2 Native session: every stall row of `episodes.csv` has the `stall_*` columns filled and
  the old rows keep empty cells after the one-time header upgrade.
