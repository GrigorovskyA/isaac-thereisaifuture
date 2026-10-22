# Evidence: native frozen collection-gap audit

- Date: 2026-10-21, Europe/Amsterdam, UTC+02:00.
- Native source revision f7f04346693c39983ecbf22046d0c4d465aebe7e. No source edits
  during native execution. Subsequent trainer journal-error cleanup is described below.
- Scope: finite frozen policy with three deliberate collection gaps. No optimizer,
  learning, new lineage, model migration, save edit or New Run.
- Python3.12.14, existing RL packages; bridge mod0.5.0-dev, Lua5.3, no extender.
  Installed game version/Steam build unavailable from the API.

## Plan and execution

One gpt-6-luna/high script worker ran the exact prepared command once; zero retries:

```powershell
& D:\isaac\.venv\Scripts\python.exe -u D:\isaac\reports\local\native-fresh-rollout-20261021\diagnostic.py --run
```

Working directory D:\isaac, PYTHONUNBUFFERED=1. Helper SHA256
ebe275c5747a5bdd951722893b7bfe656418a1723f69fd58cf6f3c936700593d.
Assignment SHA256a9dfc8ee95fa24eb81250e34d5f2500ea3445777cb6edd8ddc9869bcda53e65e.
Start cutoff1792604572.2703311 Unix, action stop1792604692.2703311,
cleanup stop1792604737.2703311. Four-minute inclusive preparation window;
runtime at most180s,1200 decisions,1GiB including preserved run root,64MiB trace.
Stop on first death, any infrastructure fault, budget or900 sampled updates without
registered progress. Approval max_restarts1 is the schema minimum; no restart was
permitted or observed. Existing first-party Lua unchanged; no deployment needed.

Native fresh log confirms Continue/file2; no New Run. Active Isaac/type0 verified
before gameplay. Frozen original conservative-v2 t21760,seed20,config hash
7d53f55f92aae137da716f2916e4cc18db2c2594ef76bb58d2104bdb1e7ce4ee received only the
old649 observation prefix; full723 observation and v4 shadow reward were recorded.
No normalizer statistics or optimizer were updated in this native check.

After decisions64,128,192 the helper invoked the production gate's
end_collection_segment, strictly released input, waited one second, called the
normal gated reset and reset frozen recurrent state. The synthetic actual-SB3
checks separately exercise the trainer callback/public force-reset path.

## Results and primary readback

| Check | Exit | Status | Evidence |
| --- | --- | --- | --- |
| Bounded native audit | 0 | passed | 278 decisions,3 refreshes,63.963s including setup/cleanup |
| Deliberate idle gap refresh | 0 | passed | Three36-frame gaps; first commands lag0/0/1 frame |
| Paired trace/schema reconstruction | 0 | passed | 278 pairs/556 endpoints,723-vector and original649 prefix match exactly |
| Native accepted actions | 0 | passed | 278 actions match ordered frame/session/epoch/directions;246 lag0,32 lag1 |
| Unknown gap accounting | 0 | passed | 900 sampled native updates plus108 idle updates; no fabricated gap samples |
| Shadow reward persistence | 0 | passed | Exact0.06170311686765427 replay;237 stationary pairs paid0 |
| Frozen artifacts | 0 | passed | All76 source/deployed/config/helper/model/normalizer/latest hashes unchanged |
| Owned cleanup | 0 | passed | Native release/observer close/shutdown; process/listener/approval absent |
| Native optimizer/learning improvement | n/a | not_run | Frozen-delay boundary audit only |
| Final offline follow-up | 0 | passed | 149 targeted/2292 full tests,zero failures/skips;51 strict items;CPU smoke16 steps |

Primary ran analyze-gaps.py,verify-native.py,analyze-geometry.py and independent
hash/timestamp/span readback, all exit0. Local evidence under
reports/local/native-fresh-rollout-20261021 includes gap-analysis.json,
geometry-analysis.json,primary-native-verification.json,primary-summary.json,
native-game-log.txt and session raw traces. Raw local logs/artifacts stay outside Git.
Worker assertions alone were not acceptance evidence.

| Boundary after decision | Old frame | Fresh frame | Unknown frames | Gap seconds | First action lag |
| --- | --- | --- | --- | --- | --- |
| 64 | 58243 | 58279 | 36 | 1.188 | 0 |
| 128 | 58486 | 58522 | 36 | 1.171 | 0 |
| 192 | 58724 | 58760 | 36 | 1.172 | 1 |

Every next diagnostic before frame equals the refreshed gate frame. Previous
sampled after frames equal the recorded pre-gap boundaries. Record IDs remain
1..278 with no inserted transitions. Native action sequences increase with gaps
for actual release commands; they are not incorrectly equated to trace record IDs.
All accepted actions match ordered identities/directions and bounded frame lags.

Session0ef2c048aa1f42638de97265c4f33a51,epoch1,frames58034->59042,
updates6->1014. Total span1008=900 sampled+108 unknown idle updates. Four gate
handoffs accepted,zero rejects/races/observation gaps/withheld actions; outcomes
remain empty,so collection boundaries were not counted as deaths or clears.
The progress guard stopped at900 sampled updates; actual damage coverage is partial.
This completes a short boundary audit, not a five-minute training-duration stage.

## Preservation and limitations

All76 frozen hashes were checked by primary before follow-up edits, including v2
t21760 and v3t24064 triplets/latest pointers. No checkpoint was published. The
normalizer and model hashes remain unchanged. Cleanup errors empty, no Isaac
process,9528 listener,owned approval or temporary approval; native successful
shutdown and observer close confirmed. Runtime roots597639763 bytes,below1GiB.

V4 shadow reward remains collector-local and retained across all three refreshes;
237 stationary pairs paid0,12 movement pairs paid positive bonus.497/556 endpoints
lack interpolation support. Neither larger reward nor corrected frame freshness
proves escape from the corner, improved damage or clears.

Primary self-review using openspec-verify-change accepts task2.1: the installed-game
boundary mechanism reacquired fresh eligible input after deliberate idle movement
of the game clock. Actual PPO/RecurrentPPO normalization/recurrent accounting is
covered by synthetic tests. These are complementary scopes, not native optimizer
qualification. Both added requirements and all3 scenario groups are covered at
these declared levels. No known implementation issue remains after the final gate;
change4/4,unarchived. This is self-review,not independent review.

After the native audit, self-review moved the initial collection-contract journal
write inside the trainer's existing finally-protected scope. A regression checks
journal failure closes the environment before any reset/action. This touches only
trainer setup error cleanup, not the audited callback/gate/reset implementation.
Final bounded offline checks are recorded separately; no second game run was needed.

Remaining limits: within-rollout inference delays, ungated live mode, real optimizer
load and longer sessions are not broadly qualified. Recurrent memory is intentionally
segmented at rollout boundaries. Next prepare an explicit compatible723-input model
lineage/transfer plan, then a separately declared five-minute learning comparison
of damage dealt/taken and verified clears. No automatic resume,New Run,15-30min,
hour or four-hour escalation follows from this check.

Final offline runner:reports/local/fresh-rollout-check-02/run.ps1,helper SHA256
70b7a0a137cfbd03e941e32694a1f69c1fd8119db56d242090aeb09e6fd76068;
649-input manifest SHA256799ab0b600627ad16cb1690a2fb1de4b85034fb079b542f1e4a469c0ed0e72e6.
Fixed stop1792605550.881 Unix,2GiB,zero retries/native actions. Actual result0,
149 targeted/2292 full tests,zero failures/skips,51 strict items,mypy62 source
files,pip consistency and CPU smoke16 steps all passed. Primary read saved logs and
independently rehashed all649 final inputs with zero mismatches. The final source
difference from the native revision is solely trainer startup journal-error cleanup;
the gate/callback/native boundary path and both original models remain unchanged.
