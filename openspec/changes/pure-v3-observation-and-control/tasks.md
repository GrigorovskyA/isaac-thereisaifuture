## 1. Implementation

- [x] 1.1 Observation schema 4 in Lua and Python (stats, tear flags, weapons, own attacks, bombs) and 32 KiB messages; verify validation, encoding size, oracle separation and worst-case size.
- [x] 1.2 Action repeat 6, use-head prior, reward v4 and the `pure-v3` lineage config, launchers, dashboard default and docs; verify prior probabilities at creation and that `pure-v2` checkpoints are refused.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [ ] 2.2 Windows `scripts/Check.ps1` and redeploy `mod/observer`.
- [ ] 2.3 Short native check: plausible stats/flags/weapons, own tears and a placed bomb visible in frames, accepted use press, stall and death restart, reloadable checkpoint.
