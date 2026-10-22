# Evidence: callback-probe-procedure-01

- Date/time and timezone: 2026-10-17, Mac executor (documentation only)
- Git revision and dirty status: on top of 0fe5a58; new files uncommitted
- Change scope and acceptance criteria: reviewable bounded procedure for the first
  callback-order probe of observer 0.4.1-dev; no runtime actions, code, or deployment.
- Game/mod/bridge versions: installed 0.4.0 (unchanged); trace bundle 0.4.1-dev,
  `callback_trace=true`, not installed.
- Python/package versions and configuration hash: not applicable.
- Scenario, split, seeds, budget, and stop conditions: one `action_probe --sequences 1`
  at most; trace 10 s / 512 attempts; action lease <=120 s.

## Sources inspected

`cli.py` (observe flags: `--accept-timeout`, `--samples`, `--confirmed-save-slot`, ...),
`launcher.py` (`preflight` compares installed files to default-off source; game launched
with temporary `--luadebug`), `action_probe.py` (required `--approval`,
`--confirmed-save-slot 2`, `--output` opened with `x`; `--sequences` 1..50; case 1 is a
two-frame left pulse, then neutral and release), `docs/SAFE_ACTIONS.md` (approval fields,
30-minute expiry, 120 s lease), `actions.py` (`ActionApproval`), the Lua trace source, and
`reports/2026-10-17-entity-observation-v1.md` (accepted 0.4.0 hashes).

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Procedure written | `docs/CALLBACK_TRACE_PROBE.md` | - | passed | exact flags resolved against source |
| Bundle hashes recorded | from task text | - | passed | not re-hashed; bundle not read or mutated |
| Launcher gate not relaxed | design | - | passed | manual `--luadebug` launch specified instead |
| Probe, deployment, game run | - | - | not_run | prepared only; standing bounded-action permission, manual closure/current-instance checks pending |
| Task 4 subchecks (shooting, terminal/death, revival/events, reset, 100 episodes, RL inference) | - | - | not_run | outside this probe |

## Real game

Not run. Isaac PID 39624 was not touched.

## Limitations and continuation

- Likely truncation: render/update enter/exit records can consume the 512-attempt budget
  within seconds at 60 fps; the procedure requires reporting it.
- Hello must report `0.4.1-dev` (checked in step 5, not assumed).
- Install path convention `<Game>/mods/isaac_threrisaifuture_observer/` taken from
  `launcher.MOD_DIRECTORY`.
- Blocker: game PID 39624 was still running at primary review, awaiting manual normal
  exit; no probe or deployment ran. Source inspection is not runtime acceptance; the
  746-test baseline is unchanged.
- Revision 02: roadmap item corrected to 05; human vs orchestrator roles clarified;
  step 4 now continues the existing run; leftover approval removed before first
  launch; normal cleanup installs default-off 0.4.1-dev (main.lua
  `669918a7...cb21634`) so launcher preflight can match source; 0.4.0 rollback
  explicitly keeps the source-hash mismatch; log location taken from
  `COMPATIBILITY_AUDIT.md`.
- Next action: user review, then an authorized run after manual normal exit.


## Primary verification and self-review

- Reviewed at 5e64e4f plus these documentation artifacts, 2026-10-17,
  Europe/Amsterdam. Exact flags checked against cli.py/action_probe.py;
  default-off source and trace-on bundle hashes checked against prepared files.
- Source facts and corrected manual roles, Continue preservation, approval timing,
  temporary manual launch, private bounded logs and cleanup/rollback version
  alignment are accepted. Clarified that the Python probe exits while Isaac
  stays open; forced reset/training are outside authority, not pending probes.
- `./scripts/OpenSpec.ps1 validate --all --strict`: exit 0, 24/24.
  `git diff --check`: exit 0. Documentation-only batch; unchanged code's full
  Check.ps1 baseline is 746 passed/no skips, recorded in trace evidence. No
  additional tests were warranted for these documentation corrections.
- Important current limitation: installed 0.4.0 differs from repository 0.4.1-dev;
  source-hash launcher preflight is expected to refuse until a reviewed matching
  default-off update is installed. The trace-on bundle also intentionally differs.
  No gate was relaxed and no launcher success is claimed.
- No runtime deployment/probe has run. Manual normal game closure is pending;
  no further user question is needed because the primary already asked for it.
  Task 4 and item-05 real acceptance remain unfinished.
