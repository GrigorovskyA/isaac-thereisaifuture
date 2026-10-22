# Evidence: offline native event outbox

- Date/time and timezone: 2026-10-17, Europe/Amsterdam.
- Git revision and dirty status: based on 22360fb; implementation, specs and solo workflow updates reviewed together before commit.
- Scope: bounded producer delivery bookkeeping for episode-lifecycle task 3.8; no sender or engine emitter.
- Game/mod/bridge: not run; observer source and installed files untouched.
- Python/packages: CPython 3.12.14, pytest 9.1.1; existing environment, no dependency/lock changes.
- Scenario/split/seeds/budget: deterministic offline records with fabricated game_api provenance; at most 32 pending events / 32768 encoded bytes. No gameplay or training.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Initial outbox cases | .venv/Scripts/python.exe -m pytest tests/test_native_outbox.py -q | 0 | passed | 51 cases before two producer/receipt integration cases were added |
| Full offline quality gate | ./scripts/Check.ps1 with environment below | 0 | passed | 867 tests, zero skips; Ruff, 80 formatted files, strict mypy on 37 sources, pip consistency |
| Strict complete project | ./scripts/OpenSpec.ps1 validate --all --strict (also inside Check.ps1) | 0 | passed | 24/24: eight main specs and 16 unarchived changes |
| Strict active change | ./scripts/OpenSpec.ps1 validate episode-lifecycle --strict | 0 | passed | Revised requirement validates |
| Native attach/emitter/sender | Actual Isaac event delivery | N/A | not_run | No runtime integration claimed |
| Real episode acceptance | 100 consecutive real episodes | N/A | blocked | Training isolation/start/reset and exact native timing remain unresolved |

Full-gate environment (existing isolated Lua runtime; private temporary output):

```powershell
$env:PYTHONPATH='C:\Users\<user>\Documents\Codex\2026-10-17\work-on-isaac-threrisaifuture-in-the\work\lua-test-runtime'
$env:ISAAC_JSON_LUA='C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\scripts\json.lua'
$env:TMP=Join-Path (Get-Location) 'reports\local\check-native-protocol'
$env:TEMP=$env:TMP
.\scripts\Check.ps1
```

The first full run passed 865 tests, lint/format/mypy/pip but strict OpenSpec failed
on a >500-character requirement warning. The requirement was shortened without
removing behavior; two end-to-end producer/receipt cases were added afterward.
Initial Ruff line-length findings were fixed by formatting before that full run.

## Behavioral evidence and self-review

- Explicit baseline, neutral-time capture, contiguous IDs, same-frame events,
  context mismatches, regressing/late frames and strict configured limits.
- Staged events remain counted against memory limits; future events are retained.
  Empty intervals use the committed watermark, not a future assigned ID.
- Exact serialized-byte boundary and one-byte-short rejection; actual 32-event
  boundary; overflow closes and clears rather than dropping events.
- Commit accepts the exact current batch only; equal copies, foreign batches,
  replay and missing acknowledgements fail permanently. Close is idempotent.
- Producer bytes are decoded by the existing cursor, and zero/32-event streams
  traverse the actual NativeReceiptAssembler with ack/completion/watermark checks.
- Simulated send-failure cleanup and reconnect use a fresh explicit baseline.
  This checks data cleanup, not release of real game inputs.

Self-review maps the four new specification scenarios to tests in
tests/test_native_outbox.py. Production code is isolated in native_outbox.py;
there are no observer imports, socket writes, clock calls, action permissions,
reward inference or engine hooks. Queue storage and staged references are bounded.
Frozen records retain scalar validated event data. Validated copies reject bypassed
model values. Whole task 3.8 remains unchecked and no change is archived.

## Real game

No game interaction, deployment, startup, save/Cloud/mod configuration changes,
reset or run interruption. Current instance/slot was not inspected for offline work.
Previous ordinary-profile permissions and all runtime budgets remain unchanged.

## RL evaluation

Not applicable; fabricated records establish software behavior only.

## Limitations and continuation

Sealing is the caller's assertion of event completeness. The outbox cannot prove
callback quiescence, establish an attach baseline, repair late delivery or undo
an already-consumed transition. Sender failure must separately release inputs.
See the [API audit](2026-10-17-native-oracle-api-audit.md). Next: passive callback
probe design and terminal/short-step semantics before emitter/sender integration.
Item 05 stays 12/19 complete; runtime tasks and 100-real-episode acceptance remain open.
