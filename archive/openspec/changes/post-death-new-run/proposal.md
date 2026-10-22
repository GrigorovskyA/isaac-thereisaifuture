## Why

A natural death ended the accepted runtime check,so the Continue-only agent
entry cannot start the next session. The user requested explicit automatic New Run
without screenshots before subsequent diagnostic and bounded learning work.

## What Changes

- Add explicit entry-mode new-run alongside continue/manual;default remains Continue.
- Require fresh file2 metadata and affirmative absence of a saved game before New Run.
- Use bounded local confirmations to enter the default character;require native
  [New,2] and an active bridge snapshot identifying Isaac before successful readiness.
- Preserve all existing focus,ownership,deadline,key-up and eight-key guards.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `local-menu-entry`: explicit post-death New Run with existing-run protection.

## Impact

Python menu and launcher modules,agent CMD/PS wrappers,behavioral tests and docs.
No game observer/schema changes,save edits,forced deaths,model changes or learning.
Acceptance requires offline lifecycle regression and one bounded native New Run
with confirmed file2/Isaac identity. Failures remain explicit and are not retries.
