# Evidence: post-death-new-run

- Date: 2026-10-20, Europe/Amsterdam; final gate completed 19:28, native launch 19:29.
- Base revision: fabcfe9915a9328da6d309b927a6e31beeeb3c8c plus the reviewed change.
- Scope: explicit file2 New Run after death, protecting existing Continue; no learning.
- Runtime: native Windows, Python 3.12.14, Repentance+ 1.9.7.17.J460,
  observer 0.5.0-dev, Lua 5.3, extender unavailable.
- Native budget: one launch, 180s outer/90s observer/60s menu, eight keys,
  one snapshot, 64MiB output, zero gameplay/deaths/restarts/retries/training.
- Profile: authorized ordinary file2; no isolation claim. Existing Steam options
  and installed mods were retained. No save imports/edits or Cloud setting changes.

## Results

| Check | Command/scenario | Exit | Status | Evidence |
|---|---|---|---|---|
| Menu and launcher regressions | `.venv/Scripts/python.exe -m pytest tests/test_menu_entry.py tests/test_launcher.py -q` | 0 | passed | 63 tests, zero failures/skips |
| Windows gate | `./scripts/Check.ps1` | 0 | passed | 1995 pytest tests, zero skipped; Ruff/format/mypy/pip clean; OpenSpec 36/36 |
| CMD argument override | `./Start-IsaacAgent.cmd --entry-mode new-run --preflight-only` | 0 | passed | No launch; explicit mode accepted |
| Native New Run | launcher command below, prepared finite wrapper | 0 | passed | Fresh `[New, 2]`, active Isaac, normal shutdown, 25.55s, 26100 output bytes |
| Frozen code and checkpoint integrity | Before/after SHA256 comparisons | 0 | passed | Six tested source/test/wrapper hashes identical; t8960 parent unchanged |
| Cleanup | Native log plus process/listener/approval checks | 0 | passed | Successful normal shutdown; no Isaac, port9528 listener or approval |
| RL stack smoke | No RL/dependency changes | — | not_run | Existing synthetic smoke does not establish game acceptance |

Exact native command (installed game and log passed as absolute paths):

```text
D:/isaac/.venv/Scripts/python.exe -m isaac_threrisaifuture.launcher --entry-mode new-run --samples 1 --reconnects 0 --duration 90 --connection-timeout 45 --game-directory "C:/Program Files (x86)/Steam/steamapps/common/The Binding of Isaac Rebirth" --game-log "C:/Users/<user>/Documents/My Games/Binding of Isaac Repentance+/log.txt"
```

Ignored local receipts: `reports/local/new-run-{before,after}.json`,
`new-run-targeted{,-exit}.txt/json`, `new-run-check.txt`, `new-run-gate-exit.json`,
`new-run-preflight.txt`, `new-run-native/{plan,result}.json`, console/native logs,
and `runs/observe-20261020-192907-c9d7e233/observer.jsonl`.

## Real game

Steam launched the owned installed process. Eight guarded menu keys selected file2,
confirmed New Run and the remembered character; input stopped at the run marker.
Native seed `JBMH Z9CS` (1337525505), mode `New`, slot2. The validated bridge
snapshot was active, character_type0 (Isaac), session
`5ce8ec25824d4b5eb791556463c55fdb`, epoch1/frame0, six red half-hearts/max6.
This proves startup identity, not advancing gameplay or policy quality.

The test wrapper closed its owned game normally; ordinary launcher use leaves
the game open. Primary independently checked native shutdown, process/listener
absence, source/install equality and approval absence. Both diagnostic flags
remained false. No training approval was created, and no model was initialized.
The t8960 model, manifest, normalizer and latest pointer were unchanged.

## Primary self-review and OpenSpec verification

| Dimension | Assessment |
|---|---|
| Completeness | 4/4 tasks; both added requirements implemented and evidenced |
| Correctness | 2/2 requirements, 4/4 scenarios: positive absence/start, existing or unknown state refusal, unavailable-to-Isaac load boundary, other-character refusal |
| Coherence | Shared guarded menu state machine, compatible Continue wrapper, explicit CLI modes and existing observer cleanup patterns follow design |

Mappings: `menu_entry.enter_file2` enforces absence, mode/slot and key/deadline/log
bounds; `launcher.observe_sessions` verifies active Isaac before readiness.
Behavioral tests cover initial slots1/2/3, ambiguous absence, existing Continue,
wrong run mode/slot, load boundary and wrong character. Existing foreground,
key-up, ownership and timeout regressions remain passing. CLI wrappers expose the
declared mode; the CMD override was verified through actual parsing.
No critical issues, warnings or suggestions found in this primary self-review;
this is not an independent review. All specification verification checks ran.
The scoped change is accepted and remains unarchived.

## Limitations and continuation

Only the installed profile's remembered Isaac default was verified natively.
Other characters fail after startup; arbitrary character navigation is outside
scope. Unexpected native log formats, denied foreground or physical menu
interference fail without fallback. Fault paths are offline regressions, not
induced native failures. A new game run does not reset a model lineage.

Next: native phase/champion diagnostics, then an explicit compatible learning
lineage. Legacy t8960 remains incompatible with live-conservative-v2 reward;
do not relabel or silently initialize a fresh model. No training improvement,
revival handling or five-death training acceptance is claimed here.
