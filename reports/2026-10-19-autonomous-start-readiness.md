# Evidence: agent-driven launch and training readiness

- Date: 2026-10-19, Europe/Amsterdam.
- Scope: user-requested readiness check, agent-driven Steam launch and file-2 menu navigation, read-only bridge attach, existing checkpoint reload.
- Budget: one launch, at most 10 minutes, 20 menu actions, 20 screenshots, 10 read-only snapshots, at most 100 MiB local diagnostic output. No training, gameplay actions, restart command, approval creation or deployment.
- Existing dirty project files are preserved. No delegation or new executor assignment.

## Initial checks

- Isaac was absent; Steam was running.
- `.venv/Scripts/python.exe -m isaac_threrisaifuture.launcher --preflight-only`: exit 0, installed observer hashes match source, no files changed or game launched by preflight.
- `CheckpointPolicy` reload and `verify_unchanged()` for seed 20 checkpoint `1f4a187e-s20-t4864`: exit 0; model and normalizer hashes match the prior live-training evidence. No learning or checkpoint writes.
- Existing Windows Computer Use runtime initialized and returned app/window inventory successfully.

## Runtime results

| Check | Result | Evidence |
| --- | --- | --- |
| Steam launch | passed | `Start-Process 'steam://rungameid/250900'`; one Isaac process PID 40608, effective command line includes `--luadebug` |
| Observer load | passed | Game log: Observer 0.5.0-dev registered; source-matching installed files retained |
| Window capture | passed | Existing Computer Use `@oai/sky` returned the unique Isaac window and rendered intro/title screenshots, under the 20-capture budget |
| Menu input | failed | Intro did not skip after Return/Escape/Space; at the later observed Press Start screen, Return, Space and a click did not produce a visible transition. Focus activation and a window click were also attempted. No more retries of that approach |
| File 2 / Continue | blocked | Never reached save-selection menu; no slot claim and no in-run gameplay input |
| Read-only attach | failed | `cli observe --samples 10 --accept-timeout 90 --message-timeout 3 --reconnects 0`: process exit 2, `No Lua peer connected before accept deadline`; zero snapshots, no handshake |
| Training | not_run | Readiness check only; no approval creation, live negotiation, model inference into the game, training or restart command |
| Cleanup | passed | Alt+F4 from the observed title screen requested normal close; log records observer unload and successful Isaac shutdown; process absence checked after 2 seconds; port 9528 has no listener |
| Post-check preservation | passed | Closed-game preflight passes again; latest pointer still t4864; model and normalizer SHA256 unchanged |

The observer timeout happened while no run was active and does not establish a
broken in-run bridge. `Alt+F4` caused a normal shutdown, but this OS-level shortcut
does not establish that ordinary game-polled menu keys work. The cause of ignored
menu input is unknown; insufficient key-hold duration or game-specific input
handling are hypotheses, not confirmed findings. Do not repeat blind key presses
or claim autonomous file selection from a successful launch/screenshot.

Private listener output: `reports/local/2026-10-19-readiness-observe.txt`. No raw
desktop capture is saved in the repository. Existing checkpoint model SHA256 is
`055bba9a3326c87febf296b44d58cf0d851f158a8ae9d2a1ad820320f2cbe4c6`;
normalizer SHA256 is
`8cb23fedc3f7274e474e4cb6f9bceff3f0419a7eff01d5b8e9753c6b1a96641c`.

## Implementation readiness and next action

The checkpoint/model/normalizer are loadable with the current config hash and
seed 20. The `live` CLI supports `--resume`, a finite step target, wall-time cap,
zero tolerated faults, combat gating and the existing disk budget. No dedicated
unattended session/menu runner is implemented: current `--launch` executes the
game executable directly rather than Steam and still prints a manual file-2
selection instruction. Future agent launches must continue to use Steam as
authorized by AGENTS.md; do not rely on that direct-executable launch path.

Next: implement and verify a bounded menu-only input mechanism with observable
screen-state confirmation, then file-2/Continue selection and read-only handshake.
The existing combat gate still needs fresh readiness for each fight; reliable
launch/menu selection alone would not establish autonomous navigation or sustained
training. Approximate live outcomes remain permitted for experimental learning;
native exact-outcome integration remains a separate unfinished contract.

Self-review: only menu input was attempted, game was closed normally, no third-
party mod/config/save/Cloud edit, no new runtime authority or experiment extension.
No code change or new unit test is part of this readiness report. Existing offline
1802-test acceptance is separate evidence and is not a successful startup test.
