# Proposal

## Why
The newly authorized thirty-minute pilot exhausted existing ordinary rooms without
combat. The user explicitly approved replacing that game run on file2 while
retaining t7424 learning state; current default New Run correctly refuses Continue.

## What Changes
Add explicit Python-only replacement intent, bounded Up menu selection, fresh
file2 Continue verification and exact native [New,2] verification. Defaults stay.

## Capabilities
### New Capabilities
- `file2-replacement`: separately authorized bounded native run replacement.
### Modified Capabilities
None.

## Impact
menu_entry/windows_menu and tests only. No reward/model/config/save-file edits.
Native acceptance uses one user-approved replacement, not standing reset authority.

## Risks and acceptance
Unexpected highlight/character/focus/log state stops; bridge still requires Isaac.
Offline tests cover intent, known state, slots and unexpected starts. Full gate
precedes input. No retries or automatic reset on navigation exhaustion.
