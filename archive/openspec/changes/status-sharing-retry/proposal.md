# Proposal

## Why
A native hour attempt stopped after421.547s when Windows denied status.tmp rename
with WinError5. A concurrent reader may temporarily deny FILE_SHARE_DELETE; status
publication must tolerate bounded sharing refusals while preserving honest faults.

## What Changes
Retry only Windows sharing/access replacement errors for at most1s,retaining the
old complete JSON until one atomic replacement succeeds. Persistent/unrelated
errors remain faults. No deadline extension or new gameplay authority.

## Capabilities
### New Capabilities
- `session-status-publication`: bounded atomic status sharing resilience.
### Modified Capabilities
None.

## Impact
session_runner.atomic_json/tests only,no policy/config/transport/deployment changes.
Acceptance: actual Windows held-reader regression,transient/persistent/error-type
coverage,full gate,then a separately recorded continuation inside original deadline.
