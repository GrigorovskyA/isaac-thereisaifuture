# Design

## Context

See proposal.md. Baseline specifications cover future safe actions and game
integration. This increment delivers an audit; it does not implement those systems.
The initial local install was Repentance. During the audit the user explicitly
authorized installing Repentance+; Steam completed it and launched the game from
an already queued launch. Refresh the inventory and preserve both observations.
No game input, reset, mod installation, Cloud change, or training is authorized.

## Goals / Non-Goals

**Goals:** trace claims to sanitized local evidence and pinned primary source;
separate source feasibility from runtime proof; decide the smallest next integration.

**Non-Goals:** execute downloaded candidates, install bridge/runtime mods, test
ordinary saves, or prescribe learning algorithms.

## Decisions

1. Store only summarized evidence in Git. Use aliases for paths containing a
   Windows user or Steam account ID. Do not copy raw logs, manifests, saves, or
   downloaded repositories into the project. Reproduction commands use placeholders.
2. Compare SocketBridge, The-RL-of-Isaac, Aiisaac, and isaac-rl-agent by commit,
   license, real source paths, transport, blocking, and dependencies. Audit current
   REPENTOGON/Launcher source separately because API and save behavior changed.
3. Recommend an original minimal adapter using the game's bundled LuaSocket,
   contingent on an authorized module probe on the exact installed Repentance+.
   The observation milestone does not require REPENTOGON-only callbacks. Reusing
   SocketBridge needs transport, watchdog, callback, and protocol changes; its
   feature volume is unnecessary for the initial observation slice.
4. First implementation uses protocol/observation v1, JSON newline framing,
   loopback-only Python listener, nonblocking Lua I/O, bounded buffers and work
   per callback, correct partial-send/receive handling, and fresh connection IDs.
   It reports actual game/mod versions, capability probe results, engine frames,
   player/room state, and connection faults. No arbitrary console execution,
   actions, resets, rewards, or hidden map data. These are future design decisions,
   not implemented behavior in this audit.
5. On socket/module failure the future adapter reports a capability fault and
   stops/retries at a bounded rate without stalling the game. It closes sockets
   on exit/reload. A lost connection never implies gameplay termination.
   Do not substitute another transport silently if the authorized probe fails.
6. Isolation is a prerequisite even for observation tests: launching a game can
   write progress/settings. Backups are recovery, not isolation. REPENTOGON's
   automatic vanilla synchronization and shared game state prevent treating its
   separate persistent-save filename as an isolated training profile.

## Risks / Trade-offs

- Bundled socket files do not prove loadability -> probe require and socket API
  availability only after authorization, on the exact target build.
- Latest upstream documentation differs from local runtime -> pin source commits,
  record local evidence, and keep unknowns explicit.
- Vanilla lacks extender callbacks used by candidate code -> use baseline
  observation APIs; gate optional extensions individually.
- Profile redirection or a different Windows user may still share Steam Cloud
  and the game directory -> verify the full write set and restoration before use.
- Custom adapter needs new implementation and soak tests -> accept a small,
  reviewable scope and retain existing bridge findings as comparison evidence.

## Migration Plan

This audit deploys documentation only. No game rollback is required for audit
edits. The separately user-authorized DLC install is recorded, not rolled back.
Any later mod activation must specify an artifact hash, destination, launch options,
backup/write-set verification, and disable/rollback steps before authorization.

## Open Questions

Unknown module loading, callback timing, input release, endings and deterministic
reset remain listed in the audit. They do not block the source/inventory audit;
they gate the later milestones explicitly.
