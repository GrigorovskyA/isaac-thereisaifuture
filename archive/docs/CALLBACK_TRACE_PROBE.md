# Callback-order probe procedure (observer 0.4.1-dev, trace ON)

Historical procedure: the narrow 0.4.1-dev pulse was completed on 2026-10-17;
see reports/2026-10-17-callback-trace-runtime.md. The old pending-process status
is superseded. Preserve the recorded version-specific hashes/instructions below
as historical evidence; do not repeat the accepted pulse or use these old hashes
for current deployment. Current source/installed observer is default-inactive 0.4.4-dev.
For the next passive outcome-ordering probe use ORACLE_PROBE.md and STATUS.md.
Development is now single-agent; game launch, slot selection and exit stay manual.

## Scope and limits

- Observes callback order only: `action_accepted`, `render_exit`, `input`, `update_*`
  records correlated by frame, time, update counter, and action sequence.
- Does not prove engine consumption of input, shooting, death, revival, event APIs,
  forced reset, 100 episodes, or RL inference. The 50-action acceptance is not repeated.
- Trace bounds (source, fixed): 512 write attempts (last reserved for `stop`),
  10000 ms, 300 characters per line, started only by the first accepted authorized
  action, never renewed by reconnect. Action lease: 120 s, nonrenewable.
- At 60 fps the render/update enter/exit records can use the 512-attempt budget within
  a few seconds. Coverage may be truncated; report it, do not hide it.
- `Start-Isaac.cmd` / `launcher.py` compare installed files with the DEFAULT-OFF source
  and will refuse the trace-ON bundle. Do not relax that gate; launch manually.
- Combined `entity_action_v1` stays unsupported. Do not use persistent Steam options.

## Artifacts (exact hashes)

| Artifact | SHA-256 |
|---|---|
| Trace bundle `reports/local/callback-trace-0.4.1-dev/main.lua` | `4161ccd18ba0449d7eb6dc296e3a22dcdc4eff79a32691e1b76fd96868df068e` |
| Trace bundle `.../metadata.xml` | `a066751aa5bc96dba8be581ad712d61e47e63fa8fdd3c331c2524036fca12131` |
| Accepted installed 0.4.0 `main.lua` (rollback only) | `d4d40604138fa3826970900c65033d2784c4ff61a25baeb7e42d5cf803440f4d` |
| Accepted installed 0.4.0 `metadata.xml` (rollback only) | `3a7749dffab0ddb43f496cd1688baa1c55eec5521f2ecd15a0e1e212858d9961` |
| Default-off 0.4.1-dev source `main.lua` (normal cleanup target) | `669918a74910fdbd7c34cb0caf8b3649e29c5836510b688e6d885ff83cb21634` |
| Default-off 0.4.1-dev source `metadata.xml` (normal cleanup target) | `a066751aa5bc96dba8be581ad712d61e47e63fa8fdd3c331c2524036fca12131` |

Install directory: `<Game>/mods/isaac_threrisaifuture_observer/`. Compare with
`Get-FileHash -Algorithm SHA256`; any mismatch stops the procedure.

## Procedure

1. **Close Isaac normally.** Confirm no `isaac-ng.exe` (`tasklist`). Never install or
   copy while it runs.
2. **Backup.** Copy the installed `main.lua` and `metadata.xml` to a new private
   directory under `reports/local/`; verify the two 0.4.0 hashes above first.
3. **Install.** Copy the two bundle files over the installed ones; verify both
   installed hashes equal the trace-bundle hashes. Do not edit the bundle. With the
   game still closed, delete any leftover private `action_authorization.json` so the
   first hello cannot cache an older approval. Do not touch saves, Steam Cloud, or
   persisted Steam options.
4. **Manual launch.** Start Isaac from the game directory with the temporary argument
   only (user-run PowerShell in the game directory): `& .\isaac-ng.exe --luadebug` (same temporary mechanism as the launcher; no
   persistent Steam option). Select save file 2 manually and CONTINUE the existing
   run when one is available; do not discard a run or start a new one for this
   diagnostic. Manually center the character in a safe room and release all
   controls. The `action_probe` X/Y room-boundary safety bounds stay enforced.
5. **Read-only loading and epoch check** (no approval file yet), from the project root:
   `.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli observe --accept-timeout 60 --samples 3`
   Required: the hello reports mod version `0.4.1-dev`; snapshots are `active` with a
   player and room; note `game_epoch`; no action authority exists yet. Otherwise stop.
6. **Operator confirmation.** Confirm file 2, the current instance/process, and the
   safe room (not slot detection, only manual confirmation).
7. **Private bounded approval.** Write the private, Git-ignored
   `<Game>/mods/isaac_threrisaifuture_observer/action_authorization.json` with
   `profile_id`, `profile_mode` (`ordinary_profile_exception`), `profile_evidence`,
   `slot_evidence`, `runtime_authorization` (each nonblank, <=128 characters),
   `slot` 2, the epoch from step 5, and integer Unix `expires_at` <=30 minutes ahead
   (<=2048 bytes). Bind it to this process; never reuse it.
8. **One finite probe.** Choose a new private output path (the tool refuses existing files):
   `.\.venv\Scripts\python.exe -m isaac_threrisaifuture.action_probe --approval '<installed-approval-path>' --confirmed-save-slot 2 --sequences 1 --output 'reports/local/callback-probe-<timestamp>.jsonl'`
   Case 1 is a two-frame `left` pulse, then a one-frame neutral and `release`.
   Run once; do not repeat. Python waits up to 30 s for the game connection; the
   Lua lease is 120 s. The probe never launches or resets the game.
9. **Disconnect cleanup.** Expect the Python probe process to exit and its socket to close;
   Isaac stays open and bridge-held input must be released. If it stops (`Probe stopped: ...` / exit 2 / 130), do not rerun.
10. **Remove the private approval file**, then close Isaac manually and normally.
11. **Extract trace lines** from `<Documents>/My Games/Binding of Isaac Repentance+/log.txt`
    (location audited in `COMPATIBILITY_AUDIT.md`; verify it and its modification time
    belong to this game instance). Filter only current-session `[Isaac Future Trace]`
    lines and related bounded `Action` diagnostics into a private file; do not share
    the whole log or saves.
12. **Cleanup (normal).** With the game closed, install the reviewed default-off
    0.4.1-dev source files (hashes in the table) so the installed files match the
    repository source, and verify both hashes. A bounded read-only verification of
    that install is a separate evidence step.
    **Rollback (only if the probe failed and 0.4.0 is required):** restore the backed-up
    0.4.0 files and verify the 0.4.0 hashes. The source-hash preflight then still
    mismatches repository source 0.4.1-dev, so the launcher gate will NOT pass. Never
    bypass or relax it, never claim launcher success, and never Git-revert source to
    resolve the mismatch.

## Analysis criteria

- Correlate `action_accepted`, `render_exit`, `input`, `update_enter/exit` by frame,
  time_ms, update counter, session, epoch, and sequence.
- Report whether the 512 budget or the 10 s window truncated coverage (`stop` record
  reason) and which callbacks fall outside it.
- Only observed callback order may pass. No claim of engine consumption of input.
- Any version/hash mismatch, approval problem, or unsafe room stops the run and is
  recorded as `blocked`, not worked around.

## Task 4 status

The first callback-order subcheck is `not_run` until executed. New step timing,
shooting/terminal/revival/event probes remain `not_run`; this procedure does not
complete task 4.1/4.2/4.3. Forced reset and training/RL runs are outside current
authority. The required 100 real episodes remain blocked on training isolation
and explicit lifecycle authority.
