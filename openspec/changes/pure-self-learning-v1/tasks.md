## 1. Archive and trim

- [x] 1.1 Move hint, diagnostic, native-episode and roadmap code, tests, configs, docs and open changes to `archive/`; verify no archived module name remains in `src/`, `tests/` or `scripts/`.
- [x] 1.2 Remove hint features from the core Python modules and the Lua observer; verify the offline gate with Lua suites.

## 2. Contracts

- [x] 2.1 Observation schema 3 in Lua and Python with encoding size 1837; verify wire validation, ordering, overflow, variant classes and oracle separation of `room_index`.
- [x] 2.2 Action v2 with the `use` head and one-shot press injection; verify canonical commands, stale/replay rejection, release and Lua trigger semantics.
- [x] 2.3 Reward v2 with novelty; verify each term and the exploit tests (drop and re-pickup, repeated room entry, damage then heal, coin farming, re-clear after restart).

## 3. Training and restarts

- [x] 3.1 Contract/hyperparameter split, resume from `latest`, retention and episode metrics; verify a hyperparameter change keeps the lineage and a contract change is refused.
- [x] 3.2 Restart command, unlimited approval budget and stall watchdog; verify stall truncation and restart, death restart, fault cap and pause handling over the Lua socket.
- [x] 3.3 Forever supervisor; verify back-to-back sessions resume `latest` and stop on stop file, disk cap and fault cap.

## 4. Docs and verification

- [x] 4.1 Update README, ROADMAP, STATUS, ARCHITECTURE, RL_DESIGN, RUNTIME_AUTHORITY, AGENTS and `openspec/config.yaml`; strict OpenSpec validation and full offline gate.
- [x] 4.2 Run `scripts/Check.ps1` on native Windows.
- [ ] 4.3 Run one bounded native session: schema 3 frames, an accepted use-item press, a stall restart, a death restart and a reloadable checkpoint; record evidence or keep this task open.
