## ADDED Requirements

### Requirement: Frame timing diagnostics
The observer SHALL count callbacks, snapshots and the time spent in callbacks,
snapshot capture and snapshot JSON encoding, and while streaming SHALL log one
`Observer perf` line per window of at least 10 seconds with integer key=value fields
(`window_ms updates renders snapshots update_ms render_ms capture_ms encode_ms`), then
reset the counters. The diagnostics MUST NOT change the wire protocol, snapshots,
capabilities, handshake or command handling, and MUST NOT raise into the game.

#### Scenario: One line per window
- **WHEN** the observer streams for longer than one window
- **THEN** one `Observer perf` line is logged with the counts of that window
- **AND** the next line counts only the following window

#### Scenario: Not streaming
- **WHEN** a window ends while the observer is not streaming
- **THEN** no `Observer perf` line is logged and the counters restart
