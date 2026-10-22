## Purpose

Keep live HP rewards conservative across software segments and make changed
accounting semantics explicit in training checkpoint compatibility.

## ADDED Requirements

### Requirement: Bounded live HP credit continuity
Within one bridge session and epoch, the deriver SHALL retain a per-identity HP
floor across software episode boundaries. Only observed decreases below that
floor during consecutive complete same-visit membership MAY earn damage credit.
Healing, absence and reset MUST NOT renew credit. New session/epoch establishes a
new namespace; this contract MUST NOT claim cross-process or campaign persistence.

#### Scenario: Eight segments with healed HP
- **WHEN** the same identity repeatedly heals and loses the same HP across eight software resets
- **THEN** only its first new HP loss earns damage credit, not eight payments

#### Scenario: Missing interval and reset
- **WHEN** HP is lower at reappearance or reset than the saved floor
- **THEN** lower the floor without awarding that gap, and only subsequent new lows may earn credit

### Requirement: Conservative rebaselines and bounded history
Rebaselines MUST lower the saved floor without paying unseen loss. Changed max HP
MUST disable further credit for that identity. History SHALL hold at most4096
identities without eviction; exhaustion MUST stop rather than forget credit.

#### Scenario: History bound
- **WHEN** a session would track its4097th distinct identity
- **THEN** fail explicitly without discarding an older allowance or renewing a budget

### Requirement: Explicit reward contract compatibility
Checkpoint manifests SHALL identify the reward contract independently of unchanged
wire observation/action/event schemas. Legacy manifests MUST default to combat-v1.
Live conservative training MUST require live-conservative-v2 and reject incompatible
resume before creating the environment. Frozen legacy inference MUST remain readable.
No implicit checkpoint conversion, fresh model or overwrite SHALL occur.

#### Scenario: Resume development checkpoint
- **WHEN** live conservative training requests an old combat-v1 checkpoint
- **THEN** reject explicitly before environment creation and preserve its files/latest pointer

#### Scenario: Matching contract
- **WHEN** a completed checkpoint matches config,seed,schemas and reward contract
- **THEN** training may resume and new manifests retain that contract and parent identity
