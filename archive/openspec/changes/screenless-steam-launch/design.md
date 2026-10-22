## Context

User extension (2026-10-20): local-menu-entry now adds explicitly requested local
menu-only keys to agent entry points. The no-input/manual-menu decisions below
describe this earlier increment; they still apply to the plain Python observer.

Start-Isaac.cmd already observes without desktop capture but pauses at exit and
starts isaac-ng.exe directly. The installed vanilla Repentance+ bridge does not
provide a verified file-selection/Continue API. REPENTOGON menu APIs are a
separate, uninstalled extension and are outside this change.

## Decisions

Use os.startfile with the fixed steam://rungameid/250900 URI only after preflight
and listener readiness. There is no owned game PID and no new launch option.
Keep existing bounded observation defaults. Add Start-IsaacAgent.cmd for direct
Python invocation without PowerShell execution-policy changes, plus scripts/Start-IsaacAgent.ps1
using one snapshot, zero reconnects and a configurable 5..600 second deadline;
the scripts propagate Python exit codes without a terminal pause. Preflight-only
does not launch. A first validated snapshot emits bridge_ready with session/frame
identity and save_slot_verified=false. A handshake or launch request alone is
insufficient. Disconnect closes only observation resources; gameplay stays idle.

## Failure and compatibility

Keep hash/instance/port guards, strict protocol validation and deadline cleanup.
Steam URI dispatch does not verify the eventual binary path or save selection;
readiness is bridge evidence only. Missing URI handler fails with exit 2. Never
fall back to direct executable launch, keys, screenshots, saves or new mods.
No wire, reward, checkpoint or policy schema changes. The existing checkpoint
reward-contract incompatibility remains unrelated and unchanged.

## Verification

Simulated peers verify listener-before-Steam, first-snapshot readiness, timeout,
protocol failures and cleanup. Check the wrapper with PowerShell parsing and its
preflight-only command. Native Steam startup and successful manual-Continue
handshake are distinct checks; offline tests cannot substitute for them.
