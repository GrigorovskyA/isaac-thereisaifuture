## Context

The installed vanilla game's menu API is not exposed by the bridge. A prior native
test succeeded with 300ms scan-code input. Local log startup scans all three save
slots; these initial scans must never be treated as selected-slot evidence.

## Goals / Non-Goals

Continue an existing file2 run from a fresh Steam launch with bounded local input.
No screen capture,visual recognition,new-run fallback,training or game deployment.

## Decisions

Use Python ctypes Win32 calls rather than a PowerShell child,avoiding execution
policy changes. Enumerate visible windows,verify executable path and creation time,
and retain PID/window identity. Request foreground once per press; failure stops
without workaround. Use SendInput scan codes with finally key-up. Check focus and
fresh run-start evidence during the hold. Only Enter/Escape/Left/Right are allowed.

Require a fresh bounded log after launch. One fresh "playing cutscene 1 (Intro)."
record permits one guarded Enter to skip intro; then require the final known menu-init marker.
Drain initial slot scans before input. Allow at most four Enter presses to reach
the selected file's game menu. Infer that selection only from new persistent-data
loads. If necessary Escape to file selection and move one slot toward file2;
require a fresh file2 load before one Continue press. A missing Continue state
stops; never enter a new run with additional presses. Stop on any RNG Start Seed
marker,including unexpected slot/mode. All keys remain bounded to at most8 presses,
60 seconds menu time and the original launcher deadline. Read log <=2MiB.

The listener binds before launch but handshake is performed only after verified
Continue,so no concurrent controller/input thread is required. The native log
provides run-start identity while the existing protocol validates bridge state.
This is slot evidence,not achievement eligibility attestation. Other native versions
or unexpected menus can fail explicitly. User interference is unsupported and may
race the key-up; no automation can atomically exclude physical user input.

## Risks / Trade-offs

- Focus refusal -> fail with no key-down,leave game for user; never bypass Windows.
- Unknown menu/log format -> stop within key/time caps,no blind retry loop.
- Existing game -> refuse takeover; normal closure remains an explicit agent action.
- Partial continue -> leave game open,release input/listener; no reset or forced exit.
- New Run selected unexpectedly -> one Enter may open its menu; no further Enter
  without [Continue,2],so report failure rather than creating a new run.

## Migration Plan

Opt-in --continue-file2 in Python launcher,enabled by default only in agent CMD/PS
entry points. Existing manual long observer remains unchanged. Roll back by removing
that flag. Record offline and native success/failure separately and preserve t8960.
