## ADDED Requirements

### Requirement: Isolated bounded tear audit
The observer SHALL enable tear diagnostics only with literal true during live capture, without changing wire payloads, input, reward or game entities. A nonrenewable 120-second window, 100ms pacing, 64 scanned entities, 64 lifetime labels, 1024 lines and 900-byte lines SHALL bound the audit. Errors SHALL stop only diagnostics.

#### Scenario: Disabled or malformed opt-in
- **WHEN** the option is false or any non-boolean-true value
- **THEN** perform no additional diagnostic API reads or log writes

#### Scenario: Budget, context or diagnostic failure
- **WHEN** a bound is exhausted, session/epoch/visit changes or a diagnostic API throws
- **THEN** stop diagnostics without closing the bridge or changing normal capture

### Requirement: Separate measured facts from combat conclusions
The audit SHALL record owned player tear trajectories, reported range and nearest exported target projectile-mode CheckLine results as local scalar facts. It MUST NOT classify absence as collision, damage or death, or expose these records to the policy.

#### Scenario: Owned tear sampling and absence
- **WHEN** a main-player tear is observed and later absent
- **THEN** retain sampled displacement/path, label absence without a removal cause, and ignore other owners' tears

#### Scenario: Projectile obstruction query
- **WHEN** a nearest exported target and CheckLine are available
- **THEN** record mode3 clearance and first-hit coordinates separately from walking reachability and actual tear collisions
