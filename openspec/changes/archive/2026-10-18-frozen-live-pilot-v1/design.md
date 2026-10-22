## Context

`run_live` (random/train) already owns listening, negotiation, the watchdog, death reconnects
and reward accounting. The frozen runner must reuse that stack, not copy it, and add only policy
selection, an evaluation-specific lifecycle and richer logging.

## Decisions

### Composition, not a second transport
`run_frozen_live` builds `LiveClient` and calls `make_live_env(client, run_deadline=...)`.
A small `LiveClient` subclass overrides `connect`, `take` and `drain` only to observe the
`HelloAck` of every (re)connection and the latest snapshot session/epoch; it calls the parent
methods unchanged. Command encoding, negotiation, restart waiting and reward accounting stay in
`live.py`.

### Validation order
Options are validated (finite positive bounded steps/minutes/accept timeout, nonnegative fault
budget, explicit policy kind, checkpoint arguments only for `checkpoint`), then the policy is
loaded and `verify_unchanged()` is called, then the log folder is created, then the socket
listens. A compatibility or identity failure therefore never opens the port.

### One absolute deadline
`deadline = monotonic() + minutes * 60` is computed before listening. The accept timeout is
`min(accept_timeout, deadline - now)`; `make_live_env` receives the same deadline, so reset,
paused waits, steps and reconnects cannot renew it. Before every decision the runner checks the
cap and the deadline; after `act` it checks the deadline again before `env.step`. In-flight I/O
overrun is bounded as documented in `live.py`.

### Episode boundaries
`policy.reset(seed)` is called after every successful `env.reset()`: the first segment, after a
terminal outcome (including death followed by the autonomous restart reconnect), after timeout
and after a fault-truncated step. The per-segment seed is `policy_seed + segment_index`. LSTM
state therefore never crosses a segment.

### Counting and segments
`attempted` increments immediately before `env.step`; `completed` increments when it returns
without a fault. A segment record (episode id, start/end frame, completed steps, reward return,
end reason `cleared|death|timeout|fault|stopped`) is written at every boundary; the last open
segment is written as `stopped` with its partial steps on every exit path.

### Stop reasons and status
| stop reason | status | exit code |
|---|---|---|
| `step_cap`, `deadline` | `completed` | 0 |
| `operator_interrupt` | `interrupted` | 0 |
| `fault` (any recorded infrastructure fault), `protocol_error`, `connection_timeout`, `policy_error`, `error` | `failed` | 1 |
| artifacts changed after load (checked in `finally`) | `invalid` | 3 |

A tolerated fault (`--max-faults > 0`) still makes the status `failed`. `invalid` overrides any
other status. Option or compatibility errors before listening exit with code 2 from the CLI.

### Cleanup
`env.close()` (release, then close sockets) runs in `finally`; if env creation or reset fails,
`client.close()` still runs because the client is a context manager around everything.
`verify_unchanged()` runs in `finally` after the env is closed.

### Provenance
The log records the declared operator assistance label, the HelloAck (`game` provenance is
`unavailable` unless the operator configured it), and literal `"unknown"` for the initial room
and character build, which this runner cannot observe.

## Risks / trade-offs

- `attempted - completed` includes a step that expired at the deadline before its command was
  sent; the backend checks the budget before sending, so no action is sent after expiry.
- The subclass relies on the public `connect`/`take`/`drain` signatures of `LiveClient`.
