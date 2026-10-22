# Evidence: local-menu-entry

- Date/time: 2026-10-20,Europe/Amsterdam; successful native check about15:35.
- Base revision:9dd6cc7,dirty implementation subsequently reviewed for publication.
- Scope: local menu-only file2 Continue without screenshots or agent desktop tools.
- Runtime: Steam Repentance+1.9.7.17.J460,observer0.5.0-dev,Lua5.3,no extender.
- Python3.12 project environment; no dependency,game-mod deployment or training change.
- Parent preserved: seed20,1f4a187e-s20-t8960; original manifest/model/normalizer and
  latest pointer verified against reports/local/menu-native-2/plan.json.

## Results

| Check | Exit | Status | Evidence |
|---|---|---|---|
| Initial targeted tests | 1 | failed:50 passed,one CRLF/LF failure | reports/local/menu-targeted.txt |
| CRLF-corrected targeted/full gate | 0/0 | passed:51 targeted,1976 full | reports/local/menu-fixed-*.txt |
| First native attempt | 2 | failed:waited for menu initialization while intro was still playing;zero key attempts | reports/local/menu-native/* |
| Intro regression targeted | 0 | passed:52,zero skipped | reports/local/menu-intro-targeted.txt |
| Intro full gate | unknown | log reports1977 passed;numeric exit lost,not accepted as exit0 | reports/local/menu-intro-check.txt |
| Final full gate with durable exit receipt | 0 | passed:1977 tests in45.84s,zero skipped;Ruff,format117,mypy49,pip,OpenSpec35/35 | reports/local/menu-gate-receipt.txt,menu-gate-exit.json |
| CMD preflight,PS wrapper parse | 0 | passed;no launch in preflight | reports/local/menu-preflight.txt,primary parser output |
| Second native launch/Continue/snapshot | 0 | passed:seven keys,Continue2,one active snapshot | reports/local/menu-native-2/* |
| Primary hash/cleanup readback | n/a | passed | frozen hashes,game log,parent/latest,process/listener readback |

The first failure was fixed in log acquisition by normalizing CRLF;tests were not
weakened. The native timeout exposed a real ordering issue: intro precedes menu
initialization. One guarded Enter is now permitted only by a fresh intro-playing
record. Initial slot scans remain excluded. The final source differs from the
1976-test version only by this intro handling and its regression test. The final
gate's numeric receipt resolves the earlier lost-exit evidence gap.

## Native budget and observed sequence

Each native assignment was finite and recorded before launch:180s outer wall,
90s launcher duration,60s menu deadline,eight keys,one snapshot,64MiB output,
2MiB native-log read cap,zero training/death restart/fault retry budgets. The first
attempt ended after62.96s with no run start and clean normal shutdown.

The second runner's SHA256 was
DCEA664F6F3C713A8D6AB5397CC90FCF7D815BD6A8AB0EC346F25BBFAB51B911.
Source/configuration hashes in its plan match menu-intro-before.json and current
files. The primary verified this directly after the worker returned.

Second attempt took23.34s including cleanup,with25,965 reported output bytes.
The exact keys were Enter,Enter,Enter,Escape,Right,Enter,Enter. The script observed
a selected non-target slot,returned to file selection,moved to file2,then required
fresh file2 metadata and a loaded GameState version before the final Enter.
Native log subsequently records seed F4C7 BB19 (560639867),[Continue, 2]. No
keyboard input was sent after run start. No screenshots,screen coordinates,
agent desktop calls,manual menu handoff,new-run fallback or training were used.

Handshake/snapshot session:ed1d607a7cd44c7fa2994da2ed3a6b63;epoch1,frame16743,
status active,player present. Readiness explicitly records native_continue_log
slot evidence. A single snapshot does not prove advancing gameplay or learning.
The test runner then closed its owned process by normal WM_CLOSE. Game log confirms
successful shutdown;primary verified no game process and no listening port9528.
Approval remains absent. Model,normalizer,manifest,latest and deployed default-off
observer are unchanged. No Steam options,Cloud settings,saves or other mods were
edited by the scripts;ordinary game launch/Continue can naturally save game data.

## Primary self-review and OpenSpec verification

Using openspec-verify-change for local-menu-entry;this is primary self-review,
not independent review. Read all proposal/design/delta/task artifacts and source
diff after the final tests. Added local-menu-entry requirements map to the bounded
state machine and Win32 ownership/input adapter. The modified observation-launcher
requirement maps to listener-before-Steam and default-manual/opt-in-menu modes.

| Dimension | Result |
|---|---|
| Completeness | 4/4 tasks;two local-menu requirements and one modified observation requirement mapped |
| Correctness | Offline scenarios cover stale/startup logs,slot correction,ignored keys,wrong mode/slot,missing Continue,oversized/replaced logs,deadlines,identity/focus failure and key-up on faults/run start;native success observed |
| Coherence | Manual observer preserved;agent wrappers explicitly opt in;earlier unarchived launcher artifacts aligned with user-authorized menu extension |

No critical issues,warnings or suggestions found in this scoped verification.
Behavioral input/ownership failure paths are tested with mocks;no physical focus
theft or wrong-slot run was deliberately induced in the real game. No claim that
those failures were natively exercised. No new policy/oracle/reward/checkpoint
schema or learning behavior is introduced. Synthetic RL smoke was not repeated:
no RL/dependency change;the prior smoke remains historical only.

Source references:Microsoft
[SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
and [SetForegroundWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow).
The implementation checks actual foreground identity rather than assuming a focus
request succeeded;it adds no restriction-bypass mechanism.

## Limits and next action

Continue requires an existing compatible file2 run. Missing Continue,unknown menus,
focus refusal or changed log format stop explicitly. No automated New Run path is
accepted. Native success is one installed-version/profile check,not an all-version
guarantee. Redirected Documents paths can be supplied with --game-log. On ordinary
use,the launcher leaves Isaac open after returning;normal closure here belonged
to the bounded test runner. Training is a separate gated command.

Both local-menu-entry and the follow-up acceptance of screenless-steam-launch are
complete but unarchived. The actual revival/pile membership audit remains pending,
as does explicit reward-contract lineage handling before further live learning.
