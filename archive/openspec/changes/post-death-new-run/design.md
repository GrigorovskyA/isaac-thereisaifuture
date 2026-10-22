## Context

Local Continue already verifies slot metadata,window ownership and native mode.
Historical native logs use [New,2],not [New Run,2]. The bridge already exposes
player.character_type,so no protocol change is needed to verify Isaac(type0).

## Goals / Non-Goals

Start a new file2 run after death through an explicit mode. Do not overwrite an
available Continue,add a silent fallback,select arbitrary characters,change seeds,
edit saves or start training. A new game run is not a new model lineage.

## Decisions

Generalize the menu state machine behind the unchanged continue_file2 wrapper.
An explicit new_run_file2 wrapper requires fresh selected-slot absence evidence:
the file2 gamestate missing/No Game State detected record. A loaded version or
ambiguous evidence refuses New Run before confirmation. Reuse the same native
menu defaults verified on the installed profile:New Run when Continue is absent,
then the default character confirmation. Never send another key after any run-start
marker;verify mode New and slot2. Unexpected menus/modes fail within the unchanged
eight-key/60s/2MiB limits. The new run starts the remembered character;success
requires an active snapshot with character_type0. A different character fails
without gameplay actions or a retry. There is no pre-start character-navigation claim.

Expose --entry-mode manual|continue|new-run,mutually exclusive with legacy
--continue-file2. Agent CMD supplies --entry-mode continue;an explicit later mode
argument overrides that default. PS wrapper supplies its validated EntryMode.
LaunchOptions keeps backward-compatible continue_file2 and adds new_run_file2;
both true is rejected. Plain observer remains manual. Automatic New Run readiness
waits through unavailable load snapshots within the original deadline,then checks
Isaac before reporting ready. No game process is killed by the launcher.

## Risks / Trade-offs

- Unknown save/log format -> absence unverified,fail rather than discard a run.
- Remembered character changed -> fail after startup,no gameplay/training fallback.
- Focus denied -> no key-down,no bypass. Physical menu interference unsupported.
- Starting a real run naturally writes game data -> user-authorized file2 risk;
  scripts do not edit/import saves or alter Steam options/Cloud.

## Migration Plan

Continue default is unchanged. Use Start-IsaacAgent.cmd --entry-mode new-run only
after death/no Continue. Rollback by choosing continue/manual. Record native
slot/mode/character/session and preserve model/normalizer/latest. Native test closes
its owned game normally;ordinary launcher use leaves it open for the next controller.
