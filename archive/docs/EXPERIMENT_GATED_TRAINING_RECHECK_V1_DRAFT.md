# Experiment draft: gated training recheck v1

**Status: NOT AUTHORIZED / NOT RUN.** This is advice for primary review only. It grants
no approval, deployment, runtime budget or permission to start, and it creates no files
in any session or approval directory.

Source: async-restart-training-regression-20261019-01 (macOS executor, offline only).

## Purpose

A small next pipeline check that the gated live trainer can resume a known checkpoint,
collect new real-game samples through operator handoffs, survive at most one natural
death with the asynchronous exit/start/reconnect order, finish one real PPO update and
save a reloadable child checkpoint with honest accounting. Success is not evidence of
better play.

## Proposed bounds

| Item | Bound |
|---|---|
| Parent | Known t4096 checkpoint; the primary verifies the actual latest compatible parent, config hash and seed first. This assignment did not load any private model. |
| New samples | At most 512 (t4096 to at most t4608) |
| Wall time | At most 5 minutes including operator waits |
| Handoff wait cap | 2 minutes per handoff |
| Infrastructure faults | Zero allowed (`max_faults=0` semantics; the first fault stops the run) |
| Natural-death restarts | At most one, through the existing approved restart path |
| Changes | No hyperparameter, reward, observation, action or schema changes |
| Follow-up | None automatic; no supervisor, no forced reset, no unattended resume |

## Preconditions (separate operator decisions)

- A new approval, deployment and runtime budget are separate operator decisions.
- Closed-game check, then current-slot (save file 2) identity and eligibility checks.
- The primary reruns `scripts/Check.ps1` and `scripts/OpenSpec.ps1` on Windows first.

## Success criteria

- One real gated RecurrentPPO update completes and a child checkpoint whose parent is
  the verified t4096 checkpoint reloads with its VecNormalize state.
- Rollout accounting separates checkpointed timesteps from unsaved partial samples; a
  deadline stop saves no fabricated checkpoint and never restarts from scratch.
- No action, normalization or policy call during operator waits or the restart window.
- Input released and the session closed cleanly on every stop path.

## Primary Windows follow-up

The user asked the primary to implement the IPC fix directly. The bounded fix
and full coupled tests now pass Windows Check.ps1: 1451 tests, zero skips/xfails,
OpenSpec strict 30/30. The IPC blocker and missing Windows verification below
are resolved; these are historical findings, not current failed gates. See
reports/2026-10-19-windows-gate-ipc.md. This draft is still NOT AUTHORIZED / NOT
RUN. No real-game training or parent checkpoint verification occurred here.

Current preconditions: a separate operator decision on the proposed budget,
verification of the actual compatible parent/config/seed, and current game/file-2
readiness. The original double-start cause and engine timing variation remain
known risks; one passing restart and synthetic tests do not prove their absence.

## Historical blockers and residual risks

1. The original 2026-10-18 two-start failure is still unexplained; the offline matrix
   only shows that the guards behave consistently with one dispatch per approval.
2. The asynchronous order (exit about 15 ms and start about 111 ms after dispatch) is
   modelled from one real trace; its timing variance in the installed game is unknown.
3. Windows `scripts/Check.ps1` / `scripts/OpenSpec.ps1` have not been rerun for this
   test-only change.
4. With `max_restarts=1`, a second natural death in the same run cannot restart; the
   run must stop there (expected, but the operator must know it).
5. Equivalent mutant: removing `release` only from Lua `close` is masked by the
   unarmed `action_guard` release (defence in depth). Not a defect, but record it.
6. BLOCKED on Windows: the gate's `_write_atomic` (`os.replace`) fails with WinError 5
   while an operator reads `request.json`. The same race exists in the real
   `combat-ready` path. A bounded production fix (replace retry, tolerant readers,
   no error masking in cleanup) needs separate authorization before this run.
7. Learner coverage: a tiny CPU RecurrentPPO run is verified offline over production
   Lua, loopback LiveClient, LiveBackend and CombatGateEnv (macOS only; Windows is
   blocked by item 6). Its resume uses a fresh harness, not an in-place listener reopen.
