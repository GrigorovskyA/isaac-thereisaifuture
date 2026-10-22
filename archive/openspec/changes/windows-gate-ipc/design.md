# Design

## Context

Windows readers can temporarily prevent os.replace/unlink. The gate uses atomic
request/ready files and existing absolute run/handoff deadlines. Existing tests
also expose cleanup write failures replacing the triggering exception.

## Goals / Non-Goals

Recover brief sharing conflicts, keep atomic valid files and make permanent
failure safe and observable. No widened budgets, automatic readiness, permission
repair, long retry loop or game changes. This is an offline OS/bridge contract.

## Decisions

- One typed file-operation helper retries only OSError.winerror 5/32 or the
  Windows CRT equivalent PermissionError/EACCES without a winerror, at most
  26 attempts and 250 ms, with at most 10 ms between attempts. Clip that window
  to an optional existing absolute gate deadline. Other errors propagate once.
  A spent caller deadline raises budget expiry; a spent local retry window
  re-raises the original sharing error. Check time before retrying work. Windows
  CRT open() can expose a sharing conflict as errno 13; POSIX access denial and
  explicitly unrelated Windows errors are never retried.
- Write a private uniquely named temporary file beside its target, then replace
  atomically. Bounded reads consume at most 4097 bytes. Bounded removals preserve
  consume-once/provenance checks; failure cannot authorize an acknowledgment.
  Best-effort temporary cleanup must not mask the original error.
- Reset includes initial token/request publication inside its bounded try/finally
  context, so initial I/O failure also releases and stops. Request/ack I/O uses
  the narrowed backend deadline. Recheck deadlines after polls and before resume.
- Stop releases first, sets in-memory stopped state, attempts request publication
  and token removal, then records secondary cleanup errors and summary. Secondary
  I/O failures do not replace the primary reset failure or skip env/client close.
  After expiry, cleanup gets one immediate publication/removal attempt with no
  sleep/retry, preserving the existing stopped-file contract when files are free.
  If logs also fail, retain cleanup details in memory and add them to the primary
  exception notes; broken diagnostics cannot replace that exception.
- Keep portable and real Windows tests, including transient release, persistent
  open-reader timeout, deadline clipping, non-sharing errors, ack consumption,
  failure cleanup and concurrent production reader/writer traffic. Fix the existing
  harness termination assertions so they run even when its body raises.

## Risks / Trade-offs

- Brief retries may consume time -> fixed local bounds plus original deadlines;
  fake-clock tests prove nonrenewal. No retry of arbitrary permissions errors.
- Permanently locked files cannot be repaired safely -> stop and preserve the
  original failure; neutral input and in-memory stopped state remain mandatory.
- Synthetic integration remains synthetic -> no real-game/learning-quality claim.
