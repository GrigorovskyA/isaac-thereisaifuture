## 1. Implementation

- [x] 1.1 Lua counters and the 10 s `Observer perf` log line (streaming only; the
  line does not change `note()` repeat suppression); callbacks stay under `pcall`.
- [x] 1.2 `scripts/lua_perf.py` offline parser and summary; added to the lint gate.
- [x] 1.3 Tests: `tests/test_lua_frame_timing.py` (fake clock, counts, reset, no line
  before the window or while not streaming) and `tests/test_lua_perf.py` (parser).

## 2. Verification

- [x] 2.1 Offline gate: new tests, all `tests/test_lua_*.py`, ruff, mypy and strict
  OpenSpec validation (macOS).
- [ ] 2.2 Windows native hour: redeploy `main.lua`, run one session, and read
  `scripts/lua_perf.py <log.txt>` for updates/s and the capture/encode share.
