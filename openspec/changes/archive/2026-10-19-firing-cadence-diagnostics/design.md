# Design

Reuse the existing trace lifecycle rather than create a second trace window. The
first accepted authorized action starts one nonrenewable ten-second window when
either diagnostic switch is literally true. The existing `callback_trace` keeps
its exhaustive hook behavior. The new `firing_diagnostics` switch is a sparse
firing-only mode for cadence comparisons: with `callback_trace` false, it logs
only `GET_ACTION_VALUE` for the currently commanded shooting direction, at most
once per game frame. Other hooks and uncommanded directions are skipped. If both
switches are true, the exhaustive `callback_trace` behavior takes precedence.
This avoids exhausting the shared record cap on repeated input queries while
preserving the old callback-trace use case. Sparse mode also omits per-render,
per-update and per-button release-input records; it keeps accepted actions,
native tears, explicit release and lifecycle/stop facts. Closing a sparse trace
emits one final stop record (deadline/count limits still take precedence), so a
short bounded probe does not need to keep an idle action lease alive.

Sparse shooting input records include raw cooldown values at that hook phase. A
separate `fire_tear` record is emitted only for the currently held approved
player shot, correlated by existing identity/sequence/frame/time fields. These
are callback facts, not confirmed consumed input or a maximum-rate conclusion.

Use finite numeric formatting with an absolute 1000000 bound; missing/invalid
values become na. Read/sink exceptions or recursion permanently disable only the
trace using its existing guarded machinery. No property writes. Stop records
consume the existing attempt budget; oversized records stop rather than truncate
identity. Existing close/reconnect/transition behavior and cleanup remain intact.
No diagnostics in handshake, snapshots, policy, normalizer, reward or model.

The fixed cadence probe first uses a read-only `entity_observation_v1` handshake
on the same listener. It requires an active type-0 character in the centered
bounds, no enemy or projectile in the entity frame, and no entity-feed overflow
for those kinds. It closes only that peer, retains the listener, and then
negotiates `safe_actions_v1` with the same mod instance. Before any command, the
action snapshot must match the preflight epoch, room visit, health and position.
This verifies the empty-room premise through game state and avoids rebinding the
loopback port between handshakes.

Test default-off without property reads; fractional/zero/missing/nonfinite values;
sparse once-per-frame sampling; source input and cleanup parity on failures, tear
provenance and all existing trace bounds. Full Windows Check.ps1 plus strict
validation precede offline acceptance. Real safe-room fixed-direction holds and
frozen-policy comparison
need explicit finite operator budget, active slot/instance and manual readiness.
No stat change or expiry extension is part of the experiment.
