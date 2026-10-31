## 1. Implementation

- [x] 1.1 Mode `continue-or-new` and `continue_or_new_run_file2` in `menu_entry.py`; the
  supervisor session uses it.
- [x] 1.2 Tests in `tests/test_menu_entry.py`; docs in `docs/RUNTIME_AUTHORITY.md` and
  `docs/TRAINING_SESSION.md`.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [ ] 2.2 Native: a supervisor session started on a file2 without a game records
  `menu_entry_resolved` with `new-run`, then `menu_new_run_verified`, and resumes `latest`.
