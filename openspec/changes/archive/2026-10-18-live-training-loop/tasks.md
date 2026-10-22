## 1. Specification

- [x] 1.1 Record user decisions of 2026-10-18 and the superseded rules in the proposal
- [x] 1.2 Design protocol, lifecycle, cleanup and risks
- [x] 1.3 Validate with `openspec validate live-training-loop --strict`

## 2. Lua observer 0.5.0-dev (offline)

- [x] 2.1 Training approval mode (no epoch, <= 8 h, max_restarts) and lease
- [x] 2.2 `live_loop_v1` advertisement and negotiation rules
- [x] 2.3 Oracle block (room clear, player dead, enemy HP, overflow)
- [x] 2.4 Rejected acknowledgements, heartbeat release, armed through game end
- [x] 2.5 Restart budget/interval and approval kept across restart exit
- [x] 2.6 lupa tests for 2.1–2.5 and unchanged legacy modes

## 3. Python (offline)

- [x] 3.1 `ObserverConfig.live_loop` and live snapshot decoding
- [x] 3.2 `live.py`: models, `LiveClient` reader thread, `EventDeriver`, `LiveBackend`, `FaultTolerantEnv`, approval writer
- [x] 3.3 Unit tests for the deriver, backend and fault wrapper
- [x] 3.4 End-to-end test: real `main.lua` (lupa) + real `LiveClient` over loopback with death, restart and reconnect
- [x] 3.5 CLI `approve-training` and `live` (random/train), `configs/training-live-v1.yaml`, `Start-Live.cmd`
- [x] 3.6 macOS gate `scripts/check.sh` passes

## 4. Documentation

- [x] 4.1 `docs/LIVE_LOOP.md` operator guide; STATUS, ROADMAP, README, AGENTS, metadata version
- [x] 4.2 Evidence report and `subagent_report.md` entry

## 5. Windows and real game (not run on macOS)

- [x] 5.1 `./scripts/Check.ps1` passes on Windows (1224 cases, zero skips; strict 25/25; primary review corrections recorded)
- [x] 5.2 Closed-game deployment of `main.lua`/`metadata.xml`; preflight hash match (2026-10-18 deployment evidence)
- [x] 5.3 `approve-training` written; hello lists `live_loop_v1`; oracle HP values plausible (first real random check; raw values remain uncalibrated)
- [x] 5.4 Random-policy live run >= 2000 steps with damage events, a death and an autonomous restart, zero protocol errors (operator-assisted room navigation; not autonomous navigation evidence)
- [x] 5.5 Short budgeted `live --mode train` run saves a checkpoint (real 256-step run; saved model/normalizer reloaded offline)
