## 1. Implementation

- [x] 1.1 Reward v3 ledger, stall term and config; verify each term and exploit tests (idle stall vs fight, standing still, revisits).
- [x] 1.2 Episode summary additions and train.csv callback; verify columns and that write errors never stop training.
- [x] 1.3 New `pure-v2` lineage config and launcher defaults; verify pure-v1 is refused and preserved.
- [x] 1.4 Dashboard training-statistics, action mix, exit rate, throughput; verify API and rendering.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [x] 2.2 Windows `scripts/Check.ps1`.
- [ ] 2.3 Native `pure-v2` hours: report return by outcome, exit rate, damage dealt and taken versus the first pure-v1 episodes; keep open if absent.
