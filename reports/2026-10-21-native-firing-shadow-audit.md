# Evidence: native firing shadow audit

- Date:2026-10-21, Europe/Amsterdam.
- Revision:f709a88ed16aa5493f5715e1acf586b35ec9d53a.
- Experiment:frozen t21760 deterministic inference, original live-conservative-v2
  policy/normalizer, experimental live-firing-v3 shadow reward only. No learning,
  optimizer update, migration or checkpoint publication. Continue/file2 only;
  absent Continue stops. No New Run authority.
- Prepared helper:reports/local/native-firing-20261021/diagnostic.py,
  SHA2563e42f9c79fc6e03d91031335628233ea2b0ac1ea66bdc98c76c35bf4d6e9d44b.
- Primary deployed only this repository's observer main.lua while game was closed,
  with local backup/readback. Deployed SHA256
  34c8063f60e6d2f7d680d01e50e508d88c901f7295599ecfe9d501ded0dd87a5;
  metadata unchanged00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997.
- Parent7d53f55f-s20-t21760,seed20,config7d53f55f92aae137da716f2916e4cc18db2c2594ef76bb58d2104bdb1e7ce4ee.
- Global maximum300s inclusive setup; absolute action stop1792587971.122995 Unix,
  cleanup stop1792588016.122995;20000 decisions,1GiB disk,64MiB trace,1800 native
  updates without registered damage/clear, first-death stop, zero runtime faults
  or retries. No renewal of the original action/cleanup budget.
- Prepared initial command accidentally included a trailing dot. Parser exited1
  before any session/approval/game launch. Primary explicitly corrected the command
  and launch window inside the unchanged original absolute action/cleanup budget.
  Fresh Luna/high worker02 received one corrected invocation, no runtime retry.

Exact corrected entry command:
`& D:\isaac\.venv\Scripts\python.exe -u D:\isaac\reports\local\native-firing-20261021\diagnostic.py --run`
with PYTHONUNBUFFERED=1. The helper owns approval/hash verification, Steam launch,
guarded menu-only selection, structured bridge actions and normal owned cleanup.

## Results

| Check | Exit | Status | Evidence |
|---|---|---|---|
| Initial malformed command |1|failed|Parser refused trailing dot before any session/game/approval |
| Corrected frozen audit |0|passed|561 decisions; diagnostic stop after1800 native updates |
| Paired raw/policy trace validation |0|passed|561 pairs, original encoder vectors reproduced, no detected leakage/identity mismatch |
| Native geometry/reward replay |0|passed|1122 endpoints, all plain_tears/range260, five clear cells, no overflow; live reward equals replay |
| Primary frozen artifacts |0|passed|66 hashes unchanged, including source/config/model/normalizer/manifest/latest |
| Primary native action join |0|passed|561 native accepted commands, matching session/epoch/sequence/directions;503 frame lag0,58 lag1 |
| Owned shutdown |0|passed|Native successful shutdown/observer close; independent process/listener/approval absence |
| Full five-minute sustained stage |n/a|not_run|Progress guard stopped early; no duration qualification |
| New reward training/improvement |n/a|not_run|Frozen policy only; no update or new lineage |

Local result:reports/local/native-firing-20261021/session/result.json. Primary
read the actual saved logs and ran analyze.py, analyze-firing.py and verify-native.py;
all exited0. Saved analysis.json, firing-analysis.json and
primary-native-verification.json record the independent readback. Raw logs remain
local, excluded from Git.

## Native identity and observed effects

Fresh native menu evidence confirmed file2/Continue; active characterIsaac/type0
confirmed before gameplay. One session8fb2cf108089485c96743a2d304f9101,epoch1,
visit0,frames46358->48158,updates6->1806. Mod0.5.0-dev,Lua5.3,no extender;
game version and Steam build unavailable. Protocol/action/schema1 unchanged;
firing_geometry_v1 explicitly negotiated.

All1122 sampled endpoints reported ordinary tears, measured TearRange260, a visible
vulnerable target and five positive native CheckLine(mode3) candidates. No candidate
overflow. Python independently found valid bounded walking paths/range/alignment
for all sampled endpoints. The geometry API path works for this ordinary-tear
scenario; this is not qualification of special weapons, every room or actual hit
delivery. Positive query witnesses establish the measured line criterion, not
that the frozen policy aimed at or hit that enemy.

There were12 movement pairs above0.5units, including8 positive novelty bonuses;
549 pairs at or below0.5units earned exactly zero. Total firing bonus was
0.04201174895021671, reproduced exactly from saved endpoints and below the0.25
room allowance. Total combat reward was-0.5579882510497838 including this bonus.
One room-history record; no ledger restart. This confirms native reward plumbing,
movement sensitivity and no credit for the observed stationary behavior.

The policy selected left8 times/down553 times and shot up561 times.549/561 endpoint
poses clustered near(417,290); coarse45degree aim alignment was0/561. This is a
different native start/state from the previous diagnostic, not a paired comparison
or evidence of regression/improvement. It remains the same frozen model.
Raw endpoint HP-loss lower bound0, observed player-health loss0 and clear edges0;
coverage is partial, so actual damage is unknown. One software episode had outcome
unknown, not a death/clear. No inferred kill from enemy disappearance.

The1800-update no-progress window ended collection before another action. Rewards
were logged from Unix1792587833.1424873 to1792587893.0541039, approximately60s
combat; this does not complete a five-minute duration stage. The overall script
started1792587805.806333 and finished1792587895.9633183, well inside the original
action deadline. No fault, observation gap or withheld action was reported.

## Preservation and cleanup

Original t21760 manifest hash9b39fce4114aa333f67abfcf8bd061936735b5f2b0841171a5e86122655f9f14,
model045f96ac5ae34c3d5db7584f3642dc5ed823fa4496d838ee416994fa6e64fca2,
normalizerca30e667a81cee27faac5e6229fb2e7d02f13d77596b02896be272b7788b06f7
remained unchanged. Policy identity still records live-conservative-v2. The shadow
v3 reward was never used to train or relabel that checkpoint.

Owned normal shutdown succeeded; native log confirms observer closure and successful
game shutdown. Worker exit0,cleanup_errors empty. Primary separately verified no
Isaac process, no listener9528, no owned approval or temporary approval. The first-party
observer update remains deployed, with its feature off unless negotiated; no game
save import/edit, launch-option/Cloud modification or third-party mod was performed.

## Verification and continuation

Primary self-review against firing-position-shaping task2.1: ordinary-tear native
telemetry and shaping-component audit passed, including positive and stationary
samples. Implementation tasks1.1-1.3 and native2.1 accepted,4/5; task2.2 remains
incomplete and the change stays unarchived. The original full offline gate remains
2269 tests/zero skips,49 strict items and passed synthetic smoke; no source changes
were made during or after the frozen native assignment.

Next:declare a compatible v3 lineage and budget before any learning; preserve t21760
and parents. Compare actual damage dealt/taken and verified clears under comparable
starts, first5min then15-30min. Collector-local novelty state does not provide exact
external-restart reward-state continuation. There is no automatic learner resume,
New Run or claim of improved play from this audit.
