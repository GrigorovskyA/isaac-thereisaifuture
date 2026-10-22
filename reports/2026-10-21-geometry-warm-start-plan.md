# Evidence and experiment plan: geometry-policy-warm-start

Closed:the single pilot completed; see [results](2026-10-21-geometry-training-pilot-results.md).
No standing resume or replacement-run authority remains. Preparation details below
retain their original scope.

Date2026-10-21 Europe/Amsterdam. User explicitly requested launch after geometry
and freshness qualification. One five-minute pilot only; no automatic escalation.
Original v2t21760 and v3t24064 remain immutable. Generic incompatible resume is
still refused. Source base2d0d38e3f22ea56d533e9bab0c7764ed39c45962 plus this diff.

## Explicit migration

Use conservative-v2 7d53f55f-s20-t21760,not v3t24064 trained under the defective
objective. New root runs/live-geometry-v4-pilot-20261021,initial checkpoint
10cb7030-s20-t21760,seed20,config configs/training-live-geometry-v4-pilot.yaml,
SHA25610cb703000aff1f3f6291e43c41f7a0c932f59b76c865b30b542d0050804eea0.
Observation schema2(723),reward live-firing-v4,collection live-segment-refresh-v1.
Learning hyperparameters are unchanged;only config status/resource budget differ.

Explicit offline primitive copies all original weights and Adam state and appends
74 zero columns to actor/critic input LSTM weights and matching moment tensors.
Unknown layouts fail before parameter publication. Original timesteps21760,
SB3 optimizer epoch counter340,Adam step1360 and RNG snapshot retained. No old
hidden recurrent state is transferred across this new collector boundary.

Prefix observation mean/variance and shared count21766.0001 remain unchanged.
New feature mean0/variance1 is an explicitly declared neutral prior with that
inherited scalar count,not measured historical feature data. This may slow new
feature normalization adaptation. Reward normalization statistics are inherited
under an explicit objective transition. No coefficient tuning is included.

Primary migrated locally only after checks. On64 recorded native policy-only
723-vectors,full recurrent deterministic actions,value and log probability match
the original649 prefix exactly(max value/logprob error0). Arbitrary74 extensions
also tested on actual trained synthetic RecurrentPPO. At initialization,the new
features do not change behavior; learning their influence is still required.

New model SHA2566cfc589a095a59f3c3e36dc14e4955a0b4a1c3977f28578118a229d48f68b797;
normalizer SHA256fdd8d523086d44af822693093ae3b5fb7ecf0724df7a911cd6b448517400c402.
The original v2/v3 model/normalizer/manifest/latest hashes were rechecked unchanged.
Local exact transfer helper/receipt:reports/local/geometry-training-pilot-20261021/
{migrate.py,migration.json}. Checkpoints and raw receipts stay outside Git.

## Offline verification and self-review

One gpt-6-luna/high runner executed reports/local/geometry-migration-check-01/run.ps1.
Helper SHA2560241a8f3cde2849a385ae24610952c92f3f45c11877cf8a43fd64ea49470fe81;
660-input manifest SHA256de3974df7d484828ffd5ba6a21313915f56d5c36c9adcf20722832acbfcbc26d.
Absolute stop1792606840.153 Unix,2GiB,zero retries/native actions. Exit0:105 targeted,
2294 full tests,52 strict OpenSpec items,lint/format/mypy63 files,pip consistency
and synthetic CPU smoke16steps all passed;zero failures/skips. Primary independently
read logs/result and rehashed all660 inputs. Native learning is not verified by
those tests. Actual synthetic32->64 resume validates723 saved optimizer/model/
normalizer while preserving old source files;649 resume remains refused.

Using openspec-apply-change/verify-change for geometry-policy-warm-start,primary
self-review,not independent review. Transfer requirement/scenarios implemented in
geometry_migration.py and covered by test_geometry_migration.py,including shape
failure without mutation. Offline tasks1.1/1.2 complete;native2.1/2.2 pending at
this receipt. No archive. Full acceptance includes the separately bounded trial.

## Single finite native pilot

Continue/file2 only;fresh Continue/Isaac proof before actions. No available Continue
means stop,never New Run. Resume only the named schema2/v4 warm start;missing or
incompatible artifacts stop rather than initialize. One300-second inclusive-startup
runtime,2GiB including run root,128MiB paired trace,zero infrastructure faults or
retries,max10 natural death restarts and10 observed deaths. Nonbinding1e9 step
sentinel;fixed wall time is the main cap. First9000 sampled native updates without
registered damage/clear also stop. No hidden practical navigation count increase.

A fresh Luna/high script worker receives exact helper/config/source/checkpoint
hashes and absolute action/cleanup deadlines after preparation. The runner owns
bounded approval,Steam launch,guarded menu-only Continue,structured gameplay,
cooperative release,normal owned close and hash-owned approval removal. No source
changes while running. Preserve all original parents and new initial checkpoint.

Native acceptance must verify schema2 inference/normalizer sizes,collection gap
freshness under real optimizer work,source/config lineage,all saved/unsaved samples,
native command joins and owned cleanup. Report every outcome and partial damage
coverage. Compare observed damage dealt/taken and clear edges separately from
shaping reward or new nonzero weight columns. Earlier pilots are descriptive
references,not matched held-out evaluations. Sparse interpolation support and one
seed/room are serious limits;no improved-play claim from a completed update alone.
No automatic15-30min/hour/four-hour stage,resume or New Run follows.
