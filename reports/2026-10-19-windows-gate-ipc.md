# Evidence: windows-gate-ipc

- Date/time and timezone: 2026-10-19, Europe/Amsterdam.
- Baseline: 9d14744 plus delivered async-regression feedback-1 diff and primary
  review notes. User explicitly requested primary Windows implementation.
- Scope: offline Windows gate IPC recovery and acceptance of the delivered
  asynchronous restart/coupled learner regressions. English artifacts only.
- Game/mod/bridge versions: no game involved; production observer 0.5.0-dev is
  executed only in isolated Lua fixtures. Installed mod unchanged.
- Python/packages: Python 3.12.14, existing locked environment, real installed
  CPU RecurrentPPO/VecNormalize for synthetic learner tests. No dependencies changed.
- Scenario/budget: transient and permanent sharing, clipped/frozen clocks,
  concurrent production readers/writers, original error preservation, callback
  scheduling and disposable synthetic t32 -> t64 checkpoints. No real models read.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Windows baseline defect | Prior full gate and isolated reader/replace reproduction | 1 / reproduced | failed | Historical review: WinError 5; coupled learner also failed |
| Focused initial regression run | pytest tests/test_combat_gate.py tests/test_async_restart_training.py | 1 | failed | 65 passed, 2 stopped-file publication failures; fixed with one non-waiting final cleanup attempt |
| Focused IPC implementation run | pytest tests/test_gate_ipc.py tests/test_combat_gate.py tests/test_async_restart_training.py | 1 | failed | 77 passed, 3 failures: two release-command assertions before any baseline and one Windows CRT access denial; corrected tests to observe release attempts and added bounded CRT handling |
| Focused corrected integration | Same focused command | 0 | passed | 80 passed in 23.40 s, before the final three deterministic clock/CRT tests |
| Full Windows quality gate | scripts/Check.ps1 | 0 | passed | 1451 passed in 42.85 s; zero skips/xfails; Ruff, 100 formatted files, mypy 42 sources, pip consistency |
| Strict OpenSpec | scripts/OpenSpec.ps1 validate --all --strict, inside Check.ps1 | 0 | passed | 30 passed, zero failed |
| Real-game gated training | Not started | N/A | not_run | Requires a separate finite experiment/current readiness; not replaced by these tests |

The full gate used the existing Lua test runtime through PYTHONPATH, the installed
resources/scripts/json.lua through ISAAC_JSON_LUA, and reports/local/check-native-
protocol for TMP/TEMP. No packages, permissions, system settings or fixtures were
installed or bypassed. Early lint feedback was fixed before the final gate.

## Implementation and requirement mapping

1. `_file_operation` retries native Windows errors 5/32 and Windows-only CRT
   PermissionError/EACCES without an explicit winerror. Other errors are raised
   once. It is bounded by 250 ms and 26 attempts; sleeps are at most 10 ms and
   clipped to the local window/current absolute deadline. A frozen clock still
   terminates by count. Local exhaustion retains the first sharing error; caller
   expiry raises budget exhaustion with the sharing cause, never a renewed lease.
2. Publication writes a unique sibling temporary file and uses atomic replace.
   Retry does not overwrite the target in place. Failed publication leaves the
   old complete target intact; temporary removal is best effort without another
   retry window. Reads consume at most 4097 bytes; oversized messages are rejected.
3. Gate request/ack reads, removal and publication use the existing narrowed
   backend deadline. Initial request publication is now inside reset's bounded
   exception path. No accepted readiness follows an unsuccessful read/removal.
   Existing nonce/session/epoch/room/freshness checks and restart guards remain.
4. Stop releases first and sets memory state to stopped. After expiry, stopped
   publication/removal each receive one immediate attempt without waiting/retry.
   Secondary failures are retained in cleanup_errors and the stopped log; logger
   failures cannot mask the original reset error and are attached as exception
   notes. close always reaches the environment/backend close via its finally.
5. Existing test-only harness joins and error assertions now run in guaranteed
   cleanup, including when the test body fails. The known-defect xfail was removed:
   a persistent Windows reader is an asserted bounded failure, and publication
   succeeds after it closes. Transient overlap is an asserted successful recovery.

## Windows concurrency and coupled learner evidence

Sixteen new IPC cases cover native 5/32 recovery, original-error retention,
atomic target preservation, deadline clipping, one final cleanup attempt,
non-sharing propagation, CRT/POSIX distinction, frozen-clock attempt bounds,
bounded reads/removals, initial failure, stop/logger failure, no accepted readiness
at expiry, actual short readers and fifty concurrent request updates with a
production write_readiness operator. All are included in the final gate.

The delivered feedback-1 learner now passes on Windows over production Lua,
real loopback LiveClient/LiveBackend/CombatGateEnv and real CPU RecurrentPPO.
The asynchronous death/exit/start/reconnect is crossed within a rollout, with
direct policy/value/normalizer/update instrumentation asserting no calls during
operator waits. Synthetic t32 reloads; resumed synthetic t64 records the correct
parent and normalizer count. The interrupted coupled rollout saves no checkpoint
and reports four unsaved samples. These are disposable test models, not Isaac
learning, real t4096 progression or a performance result.

## Real game / RL evaluation

No game launch, connection, control, deployment, approval creation/renewal,
save/settings/Steam Cloud edit, forced reset or real training. The installed
default-off mod and temporary-approval absence from the last runtime cleanup
remain untouched. No claim that the original double-start cause is fixed.

## Self-review and limits

Primary self-review, not independent review: both delta requirements map to code
and deterministic/real Windows tests. No policy/reward/schema/model/authority
change, no swallowed primary reset error, no readiness on failed file consumption,
no retry deadline renewal. Permanent file locks still fail safely and a failed
stopped-file publication can leave a stale disk record; the stopped process
cannot resume and later handoffs use fresh nonces. This limitation is documented.

Offline acceptance passes for windows-gate-ipc and the delivered async-regression
task after primary remediation. Executor write authority remains closed and the
monitor remains paused. Changes stay unarchived pending final archive review.
The draft five-minute/512-new-step game experiment remains NOT AUTHORIZED / NOT
RUN; current parent/config/seed and operator readiness still need verification
before any separate runtime decision. The old unexplained two-start failure and
engine timing variation remain residual risks, not erased by synthetic success.
