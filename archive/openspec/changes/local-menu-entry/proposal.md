## Why

The agent launcher requests Steam startup but cannot enter a run. The user now
explicitly requests local menu-only keyboard automation without screenshots or
agent desktop tools. Existing held scan-code input worked in a prior native test.

## What Changes

- Add a bounded local Continue controller with fresh native-log feedback.
- Verify the newly launched window's executable,PID and foreground before keys.
- Select file2, verify its fresh metadata load, and issue Continue once.
- Stop keyboard input on any run-start marker; require [Continue, 2] plus a
  validated bridge snapshot for successful automatic startup.
- Make Start-IsaacAgent.cmd use this mode; retain manual observation mode.

## Capabilities

### New Capabilities

- `local-menu-entry`: bounded menu-only Continue through native Windows input.

### Modified Capabilities

- `observation-launcher`: keep manual observation without input and permit the
  explicitly requested bounded menu mode. The unarchived screenless-steam-launch
  artifacts are updated to reflect this user-authorized extension.

## Impact

Python menu controller and Win32 adapter,launcher integration,CMD/PS wrappers,
behavioral tests and documentation. No screenshots,new mods,save/config edits,
training,model reset,Steam option changes or gameplay keyboard input.
