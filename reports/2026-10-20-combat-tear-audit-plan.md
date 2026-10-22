# Plan: frozen t6912 tear audit

Prepared 2026-10-20,Europe/Amsterdam,by the primary at base bdcf941a3dcb1c79a347bf16b4de77a211f07426 plus combat-tear-audit. One native attempt; no automatic retry or training.

## Commands and authority

The primary ran the offline gate first:65 targeted tests,2040 full tests,zero skipped,39 OpenSpec items passed. Primary independently read stage exits and verified167 frozen hashes. The initial launcher preflight correctly refused the older installed observer;primary deployed the reviewed default-off source while the game was closed,then preflight passed. The primary then enabled only tear_diagnostics in the installed copy while closed. No third-party mod,Steam option,Cloud or save edits.

One fresh gpt-6-luna/high script worker,small context,no nested workers:

`D:/isaac/.venv/Scripts/python.exe D:/isaac/reports/local/run_tear_audit.py`

Working directory D:/isaac. No special environment required; project Python already owns dependencies. This prepared wrapper creates its unique local output,checks all171 source/config/helper/input/model hashes in reports/local/tear-native-frozen.json,checks the installed configured observer hash and listener availability,creates one exact private live-loop approval,starts the prepared controller,launches through Steam,and calls guarded file2 Continue from fresh native evidence. No screenshots or desktop agent. A foreground refusal stops the attempt;do not bypass or retry.

## Budget and lineage

- Absolute outer deadline2026-10-20T21:30:00+02:00,also at most300seconds from wrapper start.
- Controller at most180seconds and512 decisions,action_repeat3. One deterministic frozen t6912 window;stop after first natural death. No controller reset after death and no second window.
- Max faults0,retries0. Combat gate at most90seconds,256 navigation commands,four room transitions. This existing gate may reach combat but does not replace learned combat actions.
- Approval240seconds,max_restarts1 (existing approval schema minimum);the finite controller never resets after death,so no death restart is scheduled.
- Output cap256MiB over both unique output roots;wrapper polls every0.5seconds after menu entry. Menu cap60seconds/eight guarded keys/native-log2MiB. Log audit caps120seconds,1024lines,64lifetime labels,64scan entities,100ms pacing.
- Resume inference only from runs/live-conservative-v2-extended-20261020/seed-20/checkpoints/08e0d262-s20-t6912,seed20,config08e0d2627b5cdac2d0be36ff2d19578496a58e9632defa50a67ae7a7653f2d8e. Model SHA2569b8e7eaa8aa89cc23debc82e99f26c365a24c617f63bbd6f5676b7ed350a22f4;normalizerd5ec622cf5dd653b7ac5bc8070693ddb0c5b65768f4d90c6bb3ba95ceaba6fd0. Missing/incompatible artifacts stop,never initialize a fresh model.
- No optimizer,model.save or normalization updates. Controller checks in-memory policy/normalizer fingerprints and CheckpointPolicy.verify_unchanged. Preserve all historical checkpoints/latest pointers.

## Cleanup and evidence

Worker allowed writes only reports/local/tear-audit-t6912/,runs/tear-audit-t6912-20261020/,the exact approval and its temporary replacement file,and optional reports/local/tear-native-worker.json. It cannot edit source/tests/config/helpers,install,deploy,alter saves,write Git or create further tasks. No concurrent primary game control or tested-file edits.

Wrapper normally closes only its owned Isaac window,waits for release/controller exit,and removes approval only if its hash matches the created lease. No force-kill of the game. On controller timeout it may terminate its own controller,retaining cleanup failure honestly. Primary verifies return logs,session/epoch/file2/character,model/source hashes,game/listener shutdown and approval absence,then restores default-off observer while closed.

Output records target CheckLine mode3 and its first-hit position,reported TearRange,and sampled owned tear trajectories. These are local facts,not hit/collision labels or new policy inputs. Compare measured distances and sampled HP honestly;no win-rate or training improvement claim from one trajectory. If focus or another prerequisite blocks native data,keep native acceptance unfinished and retain offline evidence.

## Fresh compatibility follow-up (prepared after first attempt ended)

The first attempt exited0 at the wrapper/controller level,400 decisions,zero faults/deaths/restarts,89.33seconds;software unknown episode boundary ended its sole window early. Native audit failed separately at frame11294 before any tear sample:30 target records,one reason=error stop,two valid CheckLine results blocked,range260,target distance488.26..488.69. This is not accepted trajectory evidence. All171 frozen files and in-memory model state matched;normal shutdown and exact approval cleanup passed. Primary restored default-off observer while closed.

Primary corrected non-scalar/unsafe TearFlags handling using unavailable raw numeric flags plus explicit type and read-only spectral/piercing queries,retaining bounded error detail. Documentation identifies BitSet128;the first native exception text was not retained,so that specific original exception remains an inference. Four new regression cases pass;final gate69 targeted/2044 full,zero skipped,39 strict items.169 hashes independently verified;default-off deployment and preflight passed while closed.

A new finite follow-up uses one fresh gpt-6-luna/high worker and exact command:
`D:/isaac/.venv/Scripts/python.exe D:/isaac/reports/local/run_tear_audit2.py`

New output roots reports/local/tear-audit-t6912-2/ and runs/tear-audit-t6912-2-20261020/. New frozen list reports/local/tear-native-2-frozen.json covers173 paths;deployment/assignment use tear-native-2 filenames. Same t6912 model/normalizer/config,512decision/180s controller,300s outer,one-death stop,no death reset,maxfaults0,retries0,256MiB output,240s/max_restarts1 schema-minimum approval,guarded Continue/eight keys/60s. New absolute deadline2026-10-20T21:40:00+02:00. Across the two explicitly prepared native attempts,max1024decisions/600s/two-death ceiling;no training or automatic repetition. Same owned-process cleanup and primary default-off restoration. Do not modify/reuse first-run evidence or renew its removed approval. Runtime follow-up is diagnosis on the now-current room,not a matched replay of its prior state.
