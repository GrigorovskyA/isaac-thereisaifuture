# Evidence: Windows review of Lua evidence and live-loop additions

- Date/time and timezone: 2026-10-18, Europe/Amsterdam.
- Git revision and dirty status: baseline 9a92e54; preserves the external agent's uncommitted changes and unrelated errors.txt.
- Scope: review task lua-step-evidence-20261018-01 plus the additional Mac-authored live-training-loop draft; fix reproduced offline defects and run the pinned Windows gate. No runtime acceptance.
- Game/mod/bridge: source 0.5.0-dev includes the reviewed 0.4.6-dev diagnostic hooks; installed observer remains 0.4.5-dev. No real game launched, attached, controlled or stopped.
- Python/packages: existing CPython 3.12 Windows environment, bundled game json.lua and test-only Lua 5.3 runtime; no dependency or lock changes.
- Scenarios/budgets: fabricated Lua callbacks, loopback simulated game and tiny synthetic PPO checkpoint tests; five new live-mode regressions use fake time/peers or temporary paths.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Original Lua evidence hooks | pytest tests/test_lua_step_evidence.py tests/test_lua_callback_trace.py tests/test_lua_actions.py tests/test_lua_observer.py -q | 0 | passed | 165 cases after primary corrections; initial submitted version passed 155 |
| Original corrected source gate | ./scripts/Check.ps1 before subsequent Mac live-loop additions | 0 | passed | 1167 cases; strict OpenSpec 24/24 |
| New live-loop baseline gate | ./scripts/Check.ps1 after rereading the updated report | 0 | passed | 1219 cases, strict 25/25, including simulated Lua/socket/PPO checks |
| Additional defect reproduction | In-memory EventDeriver/LiveBackend/fake-clock experiments | 0 | passed | Three defects reproduced despite the passing baseline suite; ignored summary path below |
| Live-mode unit regressions | .venv/Scripts/python.exe -m pytest tests/test_live.py -q with private temp environment | 0 | passed | 23 cases; five new regressions plus one strengthened overflow expectation |
| Final complete Windows gate | ./scripts/Check.ps1 with environment below | 0 | passed | 1224 tests, zero skips; Ruff, 91 formatted files, mypy 39 sources, pip consistency and strict OpenSpec 25/25 |
| Final strict and whitespace review | ./scripts/OpenSpec.ps1 validate --all --strict; git diff --check | 0 | passed | 25/25; no whitespace errors |
| Installed files | SHA256 readback | 0 | passed | Existing 0.4.5-dev hashes unchanged; no deployment |
| Deployment, private approval and live random/train runs | Not executed | N/A | not_run | No real-game training, repeated restarts or progression accepted |

## Lua evidence review

Primary corrections reproduced cross-context diagnostics and a diagnostic-induced
peer closure: a frame/pointer getter could reenter a room transition, and starting
a trace could release the hold before an unprotected hold-field access. Read/log
guards now stop and clear diagnostics before old-context output without altering
command/input handling. A logger reentry also ends the window rather than silently
continuing it. Monotonic hold-frame sampling, explicit release_superseded facts,
valid hook filtering, scalar checks and a weak-reference test strengthen coverage.

All five logger-failure paths now actually trigger their failing logger and prove
subsequent silence without closing the working peer; a permissive assertion that
could hide an unexercised failure was removed. The Mac follow-up correctly routed
supersession IDs through trace_num; that change is preserved.

These are bridge-state facts, not engine-consumption, physical-neutrality or READY
proof. Callback trace stays off by default and uses the same 10 s / 512 attempts /
300-byte nonrenewable limits. The installed mod was not replaced by either source
version during review.

## Reproduced live-mode defects and corrections

1. **Unbounded enemy history during overflow.** Ten snapshots with 64 different
   enemies each and overflow=1 retained 640 identities. Missing identities are now
   forgotten without invented damage/kills when current/previous coverage is
   incomplete. Tracking remains bounded to the current 64 IDs. A disappeared enemy
   across that gap is unknown; a new complete observation is required before a
   later complete-frame disappearance can again produce an estimate.
2. **Fatal protocol errors lost on reset.** A reader ProtocolError made connected
   false; reset called connect/accept, which would clear the failure before it was
   propagated. Reset now checks the stored failure first and raises ProtocolError
   without reconnecting. This is covered without a network connection.
3. **Run budget did not bound reset.** A fake initial reset consumed 90 seconds
   despite a 0.6-second configured budget; the budget was checked only afterward.
   One absolute deadline now reaches the backend and fault wrapper for reset,
   reconnect waits, paused stepping and retries. Expiry is not retried. Random
   runs log budget stop; interrupted training logs explicitly that the unfinished
   rollout has no new checkpoint. In-flight bounded I/O or model computation may
   finish after the deadline; no subsequent action/reset is started after expiry.

The five added tests cover bounded overflow membership, fatal pre-reset protocol
failure, initial-reset deadline propagation, no retry on expiry and no false
checkpoint claim. Existing complete-coverage kill behavior remains tested. The
overflow expectation was strengthened rather than retaining kills inferred across
an interval with missing evidence.

The new POSIX check script is stored executable with LF enforced in .gitattributes;
otherwise a Windows checkout could introduce CRLF into its shebang. Git attribute/
mode readback verifies this packaging fix; the Mac pre-check itself was not rerun
on Windows and is not substituted for the pinned Windows gate.

Ignored reproduction summary: reports/local/live-loop-review-repro-20261018.json.
It contains fabricated facts only; no actual game or approval was used.

## Check environment and limitations

```powershell
$env:PYTHONPATH='C:\Users\<user>\Documents\Codex\2026-10-17\work-on-isaac-threrisaifuture-in-the\work\lua-test-runtime'
$env:ISAAC_JSON_LUA='C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\scripts\json.lua'
$env:TMP=Join-Path (Get-Location) 'reports\local\check-native-protocol'
$env:TEMP=$env:TMP
.\scripts\Check.ps1
```

One shell invocation failed with a CLR error. A Windows PowerShell 5 fallback
refused Check.ps1 with AuthorizationManager; no execution policy was changed or
bypassed. The normal configured PowerShell 7.6.5 subsequently ran the unmodified
Check.ps1 successfully. A unit run without private TMP failed at cleanup on the
pre-existing global pytest-current junction; that run is not counted as a pass.
The junction was untouched and final checks used the private temp directory.

Readback confirms the installed 0.4.5-dev hashes:

- main.lua: 10596bb33a8a98c6d0e616700b931b35ec7aca44bb7c5b5cae094ec43ebb7323.
- metadata.xml: cfd4aa96a12d77d1104b69a2fef273f4b8f9a4b0f26b7a6823a0adf274016e65.

## Real game and RL evaluation

No real Isaac run, approval write, save/Cloud change, deployment or live training
occurred. The checkpoint test uses the production Lua/Python paths with an
explicit simulated game; it establishes pipeline compatibility, not game control,
learning, achievement eligibility or repeated-restart stability.

The Mac report records broader training/restart exceptions. They are not exercised
or granted by this review. Any runtime continuation must first resolve applicable
operator authorization, profile/slot identity, deployment and bounded budgets;
earlier ordinary-profile action permission alone does not authorize training.

## Self-review and continuation

This is primary review, not independent review. Actual diffs, mocked reproductions,
new regressions and the full pinned Windows gate were inspected. Original native
step completion/event barriers remain unfinished; neither source diagnostics nor
the pragmatic live backend completes the exact-step acceptance tasks.

Offline evidence task 3.10 is accepted (episode-lifecycle 15/22). Only Windows
task 5.1 of live-training-loop is newly checked; deployment and all game tasks
5.2-5.5 remain open. No archive, real-game learning or progression claim. Preserve
errors.txt and private logs/backups/approvals outside commits. Next runtime work
is a separate operator-directed preflight, not an automatic deployment or start.
