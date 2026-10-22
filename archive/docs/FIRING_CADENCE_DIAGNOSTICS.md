# Firing cadence diagnostics

## Purpose and activation

Read-only weapon cooldown evidence extends the existing private callback trace.
Source default remains callback_trace = false. Only literal true opts in; it
starts after the first accepted authorized action, never on read-only observation
or a rejected command. No new authority, capability or wire field exists.

Diagnostic builds must be installed only after normal game exit and process
absence, with backup/private hashes and a later default-off restoration. Launch,
file-2 selection, readiness and exit remain operator actions. This document does
not authorize deployment, game access, a new approval or a firing experiment.

## Records

Existing [Isaac Future Trace] input records retain hook/button/returned fields.
For shooting buttons they append fire_delay and max_fire_delay read from the
current controlled player. fire_tear records include these same fields after a
matching native tear callback and action guard. Both carry existing session,
epoch, room, frame, update counter, action sequence and monotonic milliseconds.

Finite raw numbers within +/-1000000 use six significant digits, including
fractional/negative/zero values. Missing, invalid, nonfinite or outside-bound
properties become na. This is a diagnostic representation, not stat clamping;
no player value is written. Values are sampled at their callback phase, not a
claim about the engine's internal firing decision. No diagnostic field reaches
policy input, normalization, reward, model or a protocol message.

The existing per-command tear evidence guard limits both normal and diagnostic
tear logging to the first four matching tears. A missing trace tear is not proof
of no shot (logging can stop, hold can expire, or another weapon may use lasers,
knives or different callbacks). Restrict the first comparison to ordinary tears.

## Bounds and failures

Existing limits are unchanged: one nonrenewable ten-second window per mod load,
512 emission attempts including a final stop record, 300 bytes per line. The
count or line limit may end the capture much earlier than ten seconds; check the
actual stop reason and captured frames. Do not treat an exhausted trace as full
coverage or renew through reconnect. Missing sufficient evidence is incomplete
acceptance, not permission to extend the window.

Diagnostic property/sink errors and recursion disable only the trace. Existing
input return values, held expiry (frame bound plus 250 ms wall bound), heartbeat,
death/transition/disconnect release and action leases remain unchanged. After
release, there is no synthetic held input; trace facts do not attest physical
keyboard neutrality. Manual operator confirmation is still required.

## Finite runtime protocol and completed comparison

- No training, optimizer, reward change or model write. Ordinary-tear character,
  file 2, safe empty room, character centered, no manual input during the check.
- At most one invocation, 30 seconds overall including readiness, 16 commands,
  zero restarts. Use one nonrenewable approval with a 120-second ceiling;
  do not use a training approval or change stats/saves/settings.
- Compare seven stationary same-direction shooting commands held for three game
  frames, one neutral command, then seven held for six frames and one release;
  use fresh observations, the same direction, and production ActionClient. Both
  stay within existing <=15-frame/250-ms holds; never force a continuous hold by
  extending expiry. Phase order and exact identities must be logged privately.
- Capture raw input phase/cooldown/native tears and actual release/reissue gaps.
  Trace count may end before both phases: report that limitation rather than
  infer a rate or repeat automatically. Stop on pause, damage, room/epoch change,
  disconnect, deadline or missing provenance. No automatic readiness renewal.
- Disconnect/release, ask operator to verify movement/shooting and exit normally;
  restore default-off source/deployment and remove the exact temporary approval.
  Record whether the trace was long enough to compare at least one natural
  cooldown cycle per phase. If not, real acceptance stays incomplete.

One separately authorized comparison was completed on 2026-10-19 and is recorded
in [`reports/2026-10-19-firing-cadence-runtime.md`](../reports/2026-10-19-firing-cadence-runtime.md).
It observed four native tear callbacks in the three-frame phase and five in the
six-frame phase, with 12-game-frame gaps in both; callback cooldown values were
10. These descriptive facts do not establish a maximum rate, lost shots, or a
causal effect of hold length. The installed build was restored to default off and
the temporary approval removed. A frozen-policy comparison, repeat, or stat
change requires a separate finite authorization; this result grants none.

## Verification

Production Lua offline tests cover fractional/zero/missing/invalid cooldowns,
input/wire independence, default-off without property access, read failures,
recursive getters, owner/held tear provenance, count/line bounds and cleanup.
Existing callback trace tests cover time/reconnect/sink failures. These validate
software contracts only; OpenSpec task 4 requires separately authorized Isaac
capture and operator-confirmed cleanup.

## Offline trace parser

`isaac_threrisaifuture.firing_trace` turns the private `[Isaac Future Trace]`
lines into a descriptive summary after a separately authorized capture. It is a
pure offline module: it opens no files, reads no logs by itself, prints no raw
line, and feeds no policy, reward, normalizer, wire schema or learner feature.
Only the Windows coordinator hands it the private log lines, and only the
summary (never a raw line) belongs in a committed report.

```python
from isaac_threrisaifuture.firing_trace import analyze_trace

with open(private_log_path, encoding="utf-8", errors="replace") as handle:
    summary = analyze_trace(handle)  # any iterable of text lines
```

- Lines without the exact prefix in the first 1024 characters are discarded
  silently. A prefixed line longer than 300 characters plus a two-character line
  ending is `oversized`, decided by length before any copy, so a huge line costs
  no allocation. Otherwise it must be printable ASCII
  `key=value` tokens with the required identity (`id`, `event`, `time_ms`,
  `frame`, `update`, `session`, `epoch`, `room`; `seq` is optional before the
  first action). Anything else is counted under a fixed category (`oversized`,
  `malformed`, `missing_field`, `duplicate_field`, `unknown_event`,
  `unknown_field`, `invalid_cooldown`, `duplicate_id`) with its line number, at
  most 16 samples. Rejection never echoes input text; free-text `release`/`close`
  reasons are reduced to a known class or dropped.
- Work and memory are bounded: ids are unique in 1..512 (the Lua cap), and at
  most 1,000,000 lines are scanned (`scan_limit_reached` flags a truncated scan).
  `max_lines` can only lower that budget; a value outside 0..1,000,000 raises
  `ValueError` before any line is read.
- Cooldown values must be finite and within +/-1e6 or the record is rejected.
  Fractions are preserved. `na` means missing, is counted as `missing` and is
  never treated as zero. Ranges are kept per source (`input.fire_delay`,
  `input.max_fire_delay`, `fire_tear.fire_delay`, `fire_tear.max_fire_delay`).
- The summary reports per-(session, epoch, sequence) event counts, commanded
  move/shoot/frame values, input hook/return phase counts, shoot-direction
  counts, and release-to-next-accept intervals. An interval pairs a `release`
  with the next `action_accepted` only inside the same session and epoch and
  room, requires the next sequence to exceed the released one, and is excluded
  (counted in `excluded_intervals`) across any new room/level, game start/end,
  close or exit record. Releases without a usable accept count as
  `unpaired_releases`. Handoff gaps are therefore never mixed with intra-run
  cadence, and sessions or reconnects are never merged.
- `incomplete` is true when the trace was stopped by a budget (`count`,
  `deadline` or `line_limit`) or has no stop record, plus any rejected record,
  id gap, extra stop, record after stop or truncated scan; `incomplete_reasons`
  names each. An explicit `stop reason=close` (the sparse `firing_diagnostics`
  mode's final record) is not a budget stop and is also a handoff boundary; it
  ends the window but shows neither firing coverage nor keyboard neutrality.
  The exhaustive `callback_trace` mode ends with a `close` event instead and
  therefore counts as `no_stop_record` unless a budget stop was reached.
- `fire_tear` records are logged for only the first four matching tears per
  held command. A group with four of them is flagged `tear_log_saturated`; a
  missing tear record is not evidence that no shot occurred.

Interpretation limits: the summary states what the callbacks logged. It infers
no maximum firing rate, shot loss, physical input consumption, hold-length
effect or improved play, and `limitations` in the summary repeats this. Use it
to check whether a capture is long enough to compare a natural cooldown cycle
per phase for task 4; that comparison and its cleanup stay a separate, human
confirmed runtime step. The `firing_diagnostics` sparse input sampling mode
keeps the same record format, so the same parser applies; its traces simply
contain fewer `input` and no `release_input` records. Trace lines from other
prefixes, such as `[Isaac Future OracleProbe]`, are ignored.
