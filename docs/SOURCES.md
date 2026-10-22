# Primary sources and research candidates

Initial tooling verification: 2026-10-17. Consult SETUP_REPORT and dependency locks
for installed versions. Listing a game repository here does not mean it has been
audited or confirmed compatible with Repentance+.

Read the [2026-10-17 compatibility audit](../archive/docs/COMPATIBILITY_AUDIT.md) for pinned
candidate commits, license/source findings and current local inventory. It
supersedes candidate assumptions below. In particular, current REPENTOGON uses
a launcher-managed v1.9.7.12.J273 runtime and automatic vanilla-save syncing;
its installation directory alone does not establish profile isolation.

- [LuaSocket TCP reference](https://lunarmodules.github.io/luasocket/tcp.html):
  timeout and partial-I/O semantics; the bundled game DLL may be older.
- [Lupa](https://github.com/scoder/lupa): isolated test-only Lua 5.3 runtime
  (local test tooling pinned to 2.6); no game ABI or socket module proof.
- [Steam Cloud](https://partner.steamgames.com/doc/features/cloud):
  synchronization lifecycle and per-game/global controls.
- [Repentance+ DLC](https://store.steampowered.com/app/3353470/The_Binding_of_Isaac_Repentance/):
  official app/DLC identity and prerequisites.
- [REPENTOGON installation](https://repentogon.com/install.html):
  current runtime version and save-version constraints.

## Tool documentation

- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md):
  project-instruction discovery and size limits; the root AGENTS file stays below 32 KiB.
- [Codex skills](https://learn.chatgpt.com/docs/build-skills): repository skills in `.agents/skills`.
- [OpenSpec installation](https://openspec.dev/docs/installation): Node prerequisite.
- [OpenSpec CLI](https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md): lifecycle commands.
- [OpenSpec supported tools](https://github.com/Fission-AI/OpenSpec/blob/main/docs/supported-tools.md):
  Codex skill invocation. Installed OpenSpec 1.14.3, its CLI/help, and generated files
  were checked locally; upstream main can differ.
- [Gymnasium Env](https://gymnasium.farama.org/api/env/): reset/step API.
- [RecurrentPPO](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_recurrent.html):
  recurrent policy support; project hyperparameters remain experimental hypotheses.
- [PyTorch local installation](https://pytorch.org/get-started/locally/): wheel/device selection.
- [REPENTOGON](https://repentogon.com/): runtime versions and capabilities.

## Candidates from the original discussion: audit required

For the final progression target, consult the publisher's [Repentance+ release
FAQ (2024-11-18)](https://store.steampowered.com/news/posts/?appids=250900&enddate=1744390716&feed=steam_community_announcements),
read on 2026-10-17. It describes online achievement requirements for new Dead God
files and disabling mods online. Reverify current-build behavior; it is historical
evidence, not a current runtime test. For possible programmatic slot selection,
[REPENTOGON SaveMenu](https://repentogon.com/menus/SaveMenu.html) documents selection
accessors. That extender is not installed here; highlighting a menu element alone
does not prove the save has loaded or that J460 is compatible. Do not install it
or assume indexing/selection semantics from the documentation alone.

| Source | Research purpose |
|---|---|
| [SocketBridge](https://github.com/EmptyEmeraldTablet/SocketBridge) | Lua/Python game bridge |
| [The-RL-of-Isaac](https://github.com/Seladus/The-RL-of-Isaac) | Environment/reward ideas and older-version limitations |
| [isaac-rl-agent](https://github.com/Monster7704/isaac-rl-agent) | Actual implementation scope of PPO |
| [Aiisaac](https://github.com/papaspamvicky-dev/Aiisaac) | Alternative transport |
| [BotCoop](https://github.com/Joaquin-Galle-ui/BotCoop-TheBindingofIsaac) | Scripted baseline if licensing permits |
| [External Item Descriptions](https://github.com/wofsauge/External-Item-Descriptions) | Item descriptions/interactions |
| [Bindings of Isaac Cheat Sheet](https://github.com/Swashua/Bindings-of-Isaac-Cheat-Sheet) | Structured item data |
| [Dead God](https://dead-god.ru/) | Reference mechanics and items |

Before reuse, record URL, commit/date, license, supported game, and actual test
results. A link alone does not grant permission to copy code or data.

Original context: [project discussion](https://chatgpt.com/share/6ad3311e-fe4c-83ed-bdad-27cab016ea2e).
The user specified the current project name and English-only project convention
in this development session. External sources may use other languages; all
project-authored artifacts remain in English.

## Post-death lifecycle references (2026-10-17)

- [Native callback reference](https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html): MC_POST_GAME_END distinguishes game-over death from endings; MC_POST_GAME_STARTED carries continued/fresh status. Installed enums.lua confirms callback IDs 16 and 15 respectively.
- [Debug console command reference](https://wofsauge.github.io/IsaacDocs/rep/tutorials/DebugConsole.html): fixed restart retains the current character; no character argument is supplied.
- [Isaac API](https://wofsauge.github.io/IsaacDocs/rep/Isaac.html): ExecuteCommand reference; [Entity API](https://wofsauge.github.io/IsaacDocs/rep/Entity.html) for IsDead.

These references inform the guarded adapter implementation; they do not prove
post-death behavior on installed J460. See the archived restart-after-game-over change and lifecycle evidence.
