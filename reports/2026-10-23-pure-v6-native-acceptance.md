# Evidence: pure-v4 wall exclusion and kill-credit-reward-v6

- Date/time: 2026-10-23, Europe/Amsterdam (CEST, UTC+02:00).
- Source commits: `c7aa49d` (all wall cells excluded), `7be28a4` (kill credit and
  previous one-hour report), both pushed to origin/main with the personal identity.
  Only unrelated untracked `tools/` remained before launch; it was not touched.
- Scope: Windows verification, closed-game deployment, preservation of reward-v5
  trial, and a fresh bounded native qualification of observation 5 / `pure-v6`.
- Game: Steam Repentance+ v1.9.7.17, ordinary save file 2, existing observer only.
  Initial guarded entry selected Continue; fresh model initialization did not reset
  the save. Later death/stall transitions started new runs through the supervisor.
- Stack: project Python 3.12 environment, RecurrentPPO, torch 2.14.1+cpu.
  Input 3499 floats, action [5,5,4], repeat 6, gamma 0.995, ent_coef 0.005.
- Contract hash: `ed954e0a5f2b064fc11634396f612bae4497fa4d2bddda5d6e16914ca67fe792`.
  Training YAML SHA256: `d3775e4e6a9ebacd36aea4df898aa61145a6cbe10191176bf36f42dcd9f399df`.
  Reward YAML/semantic contract is v6 / `pure-v6`; the manifest's generic
  `reward_schema_version` remains 1, separate from that semantic contract.
- Seed 1, native qualification only, no train/validation performance comparison.
  Timer: 900 seconds; per-session lease 28740 seconds, disk cap 20,480,000,000 bytes,
  consecutive-fault cap 5. Death/stall New Runs are permitted by the pure profile.
- Local evidence base: `reports/local/pure-v6-acceptance-20261023/`.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Windows offline gate with Lua | `scripts/Check.ps1` with isolated Lua 5.3 runtime and installed JSON decoder | 0 | passed | `check.log`: 1185 passed, no skips, mypy 31 files, lint/format/pip clean, strict OpenSpec 16/16 |
| CPU RL stack | `scripts/Smoke-RL.ps1` | 0 | passed | `smoke.log`: 16 synthetic steps, 3499 inputs, [5,5,4] actions |
| Deployment while closed | Copy only main.lua and metadata.xml; SHA256 readback | 0 | passed | `deployed-hashes.json`; hashes below |
| Preserve previous trial | Move runs/pure-v4 to runs/pure-v4-pre; create fresh supervisor folder | 0 | passed | Old reward-v5 checkpoint 9aab0d2d-s1-t18432 preserved; no deletion or resume |
| Wall exclusion | Native narrow shape 3 and L shape 12 | n/a | passed | 177 / 21 policy observations respectively, zero wall exports; ordinary rock/bomb_rock retained in L room |
| Fire / nonlethal enemy damage | Epoch 6 fire; epoch 1 HP decrease | n/a | passed | fire class and hits_fire=2; frame 2945 enemy HP 69.5 to 66, clock 0.0201444 to 0 |
| Full-HP kill credit | Epoch 6, frame 1897, entity 144 | n/a | passed | Prior max/floor [10,10], single enemy_damaged amount 10; episode 6 col_enemy_damage=6.75 |
| No killed-but-zero-damage rows | All completed episode rows | n/a | passed | Five of nine completed episodes have kills; all five have positive damage fraction and col_enemy_damage |
| Deduplication / HP bound | Audit actual derived labels per session/epoch/entity | n/a | passed | 5146 repeat-zero-floor samples; no further payment to zero-floor ids and no overpaid identity |
| Kill resets progress clock | Epoch 1 frame 2959, and epoch 6 one-shot | n/a | passed | Clock 0.00277778 to 0, and 0.0244778 to 0.00173333; no other progress labels in those updates |
| Native counters / map | Fresh run frames and episode CSV | n/a | passed | Start room 84 current+visited, neighbours known; kills, enemy/fire/own-bomb hit sources recorded |
| Death and stall New Runs | Six deaths, three stall truncations | n/a | passed | New native epochs, accepted stall restart acknowledgements; col_stall=-10 without death penalty on stalls |
| Checkpoint reload | Load saved RecurrentPPO and VecNormalize, infer on recorded native frame | 0 | passed | `checkpoint-reload.json`: ed954e0a-s1-t3072, input 3499, action [0,0,0], artifacts unchanged |
| Train timings | Six saved rollout rows | n/a | passed | rollout_seconds 111.234..122.313; update_seconds empty on first row, then 9.812..16.5 |
| Frozen working copy | Hash all tracked files before and after native session | 0 | passed | `frozen-result.json`: all 815 unchanged; passive helper hash unchanged |
| Planned stop and cleanup | Timer stop file, learner/supervisor result, process/port/mod readback | 0 | passed | exit 0, fault null, cleanup_errors [], no game/learner/supervisor/timer parent, listener or approval remains |
| Long continuation | User clarified four hours after qualification | n/a | planned | Resume latest without --initialize; timer 14400 seconds, receipt four-hour-timer.json |

Installed hashes (source and installed readback match):

- main.lua: `5e9352154a38ea4ad6b6d219d463993493cb676ba432f04fd2f3372853470315`.
- metadata.xml: `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.

## Real game

Exact entry used `Start-Pure.cmd` with the Steam game directory,
`C:/Users/Elmin/Documents/My Games/Binding of Isaac Repentance+/log.txt`, and
`--initialize`. The wrapper was `reports/local/pure-v6-acceptance-20261023/Run-Qualification.ps1`.
The new reward-v6 model has no parent. Old reward-v5 models remain in pure-v4-pre
and are incompatible with the new semantic contract. Never initialize this new
lineage again for continuation.

Session: `runs/pure-v4/supervisor/session-20261023-162308-0001`.
Timer started 16:23:08.151 CEST, fired 16:38:08.445. Session ran from
16:23:08.748 to 16:38:10.420 (901.656 seconds including cleanup).
Result: user_cancelled due to the planned stop file, learner_exit=0, fault=null,
cleanup_errors=[]. The retained stop.forever is intentional. The existing
read-only dashboard processes were left running.

Passive bounded diagnostics recorded 1726 native snapshots and 3532 policy
observations. Wire maximum sampled: 9069 bytes. The helper returned original
transport/deriver/encoder results unchanged and recorded oracle data separately;
it neither selected actions nor fed oracle data into the policy. Primary used
read-only game-window observations; gameplay came from the learner via the bridge.
Audit: `runs/pure-v4/qualification-audit/audit-35388.jsonl`.
Summaries: local `summary.json`, `credit-summary.json`.
Helper SHA256: `e791db011b11550c401972bd13022c9e10adb9b850851cbb81093effd21a9d15`.

Geometry identities:

- L room: session `dc9c8878fa0e45899bd33e1c6587b74f`, epoch 5, room 85,
  shape 12, 21 observations, rock/bomb_rock and no wall.
- Narrow room: session `b6b1a9d8de894891aeaf90c5f888256a`, epoch 9, room 71,
  shape 3, 177 observations, no wall.
- Fire and full-HP kill: session `50dedc12789e40618f356b8ec99d3c73`, epoch 6,
  room 85, shape 1. Frame 1897 credits entity 144's entire remaining 10 HP once.
  Episode 6 has one kill, damage_dealt_fraction=1.35, col_enemy_damage=6.75.
  The remainder includes ordinary nonlethal damage. Fire hit count is 2.
- Residual kill: session `df62f8e9c54b4d579d91374812bad00c`, epoch 1,
  frame 2959 credits remaining 3 of 10 HP, with no other progress label; clock
  resets to zero. Native nonlethal hits also reset it earlier in the same room.

## RL evaluation (if applicable)

Nine complete episodes: six deaths, three stalls, nine kills and two clears.
A tenth episode was interrupted by the planned stop; it is excluded from completed
CSV denominators. Six rollout checkpoints were saved (3072 steps); uncompleted
rollout work at cancellation is not represented by the final saved model.
No infrastructure faults, retries or repeated session launches occurred.
This small qualification verifies contracts and native effects, not policy quality
or improvement against a random baseline.

## Limitations and continuation

The latest requested native checks passed; task 2.3 is closed in both changes.
The previous schema-5 report's minimap checks remain supporting evidence for
unchanged map logic. Unencountered obstacle variants such as pits/spikes were not
revalidated in this sample; arbitrary weapons, all flag combinations and heavy
snapshot load remain outside this bounded check.

Self-review checked the wall export removal, killed-ring bounds/reset/oracle-only
placement, remaining-HP deduplication and reward-v5 rejection tests against the
change specifications. This is self-review, not independent review. No archive
operation was performed. Report, STATUS and tasks were edited only after shutdown.

Qualification stopped at ed954e0a-s1-t3072. The user resolved the earlier duration
conflict by requesting four hours (14400 seconds), then their own analysis.
The prepared continuation resumes this exact checkpoint through Start-Pure.cmd
without --initialize. Timer receipt: runs/pure-v4/supervisor/four-hour-timer.json;
wrapper: reports/local/pure-v6-acceptance-20261023/Run-FourHour.ps1. Runtime receipt
and session plan provide actual start/deadline/parent confirmation after launch.
Limits remain 20,480,000,000 bytes and five consecutive faults; the 28740-second
native lease is longer than this four-hour bound, so no lease rollover is expected.
Only stop.forever is removed before starting. Parent PowerShell remains open;
no ongoing agent supervision or working-copy edits are planned. This report and
STATUS are committed before that launch; subsequent runtime receipts stay ignored.
