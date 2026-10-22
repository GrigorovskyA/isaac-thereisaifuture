# Initial setup report

Date: **2026-10-17**, Windows 11. This report records completed setup and checks,
not verified game support. Run `doctor` to inspect installed package versions.
Project documentation, specifications, examples, and language policy are in English.

## Location

The project is in the `isaac-threrisaifuture` child directory of the current
workspace. Local Git was initialized on `main`. The user subsequently authorized
publishing the project to `https://github.com/GrigorovskyA/isaac-thereisaifuture`,
configured as `origin`. Dependencies and caches are ignored by Git.

## Tools

| Tool | Verified version | Source/purpose |
|---|---|---|
| Git | 2.46.0.windows.1 | Already installed |
| Node.js | 24.19.0 | Existing Codex runtime |
| pnpm | 11.25.0 | Existing Codex runtime |
| Codex CLI | 0.163.0-alpha.10.2 | Existing installation; version read without launching nested agents |
| OpenSpec | 1.14.3 | npm package in local node_modules |
| Python | 3.12.14 x64 | Separate `.venv` based on Codex runtime Python |
| PyTorch | 2.14.1+cpu | Official CPU wheel index |
| Gymnasium | 1.4.0 | PyPI |
| Stable-Baselines3 | 2.9.0 | PyPI |
| sb3-contrib | 2.9.0 | PyPI |
| TensorBoard | 2.21.0 | PyPI |
| NumPy / Pydantic / PyYAML | 2.5.4 / 2.14.1 / 6.0.3 | PyPI |
| pytest / Ruff / mypy | 9.1.1 / 0.17.1 / 1.20.2 | PyPI |

The Python snapshot is requirements-lock.txt. Torch is pinned separately in
Bootstrap so its CPU wheel source is explicit. Node transitive versions are in
pnpm-lock.yaml. Another machine needs Node 20.19+ and Python 3.12 available; this
project does not install system Python or Node.

Detected hardware: NVIDIA GeForce RTX 4070, 12 GiB, driver 610.88. The CPU torch
build reports `cuda_available=false` as expected; this does not indicate a broken
GPU. The exact CPU model was not verified because the initial environment denied CIM access.

## OpenSpec

The project is initialized for Codex with a custom profile. For a new setup, use:

```powershell
.\scripts\OpenSpec.ps1 init --tools codex --profile custom --language English --no-animation
```

Generated skills: explore, propose, apply-change, verify-change, sync-specs, and
archive-change. Files are in `.agents/skills`; the isolated profile is
`.tooling/openspec/config.json`; project context/rules are in openspec/config.yaml.
The wrapper temporarily sets XDG_CONFIG_HOME and restores original environment
variables afterward. A global OpenSpec installation is unnecessary.

Current artifact generation is explicitly English. The initial setup was later
corrected to the user's English-only requirement. All existing project-authored
content was translated, and the convention is enforced by AGENTS and a baseline
specification.

Baseline specifications: development-workflow (5 requirements), game-environment
(5), and rl-evaluation (5). These describe required future behavior.

## Verification results

| Command/check | Exit code | Result |
|---|---:|---|
| `scripts/Check.ps1` | 0 | Ruff lint/format, mypy, pytest, pip consistency, OpenSpec |
| pytest inside Check | 0 | 2 passed |
| OpenSpec validate --all --strict | 0 | 3 specifications passed, 0 failed |
| `scripts/Smoke-RL.ps1` | 0 | RecurrentPPO MultiDiscrete/LSTM, 16 steps, save/load/predict |
| Repeated `scripts/Bootstrap.ps1` | 0 | Successful rerun with dependency locks |
| Real-game integration | N/A | not_run; not implemented yet |

The smoke used a synthetic CPU environment, one instance, and 16 steps. It verifies
RL library compatibility, not Isaac learning or hyperparameter quality. Bootstrap
was rerun on the existing environment; installation on a separate clean machine
has not been tested.

## Initial execution-environment limitations

Initial venv creation stopped at ensurepip inside the Windows sandbox. Pip setup
completed through an authorized run outside it. Dependency downloads used approved
network access. Store Python was not used.

The first smoke could not write a checkpoint in sandbox TEMP. Its authorized
rerun passed, including save/load. This was a historical execution-permission
limitation, not an RL library failure; future runs follow the active permissions.

## Next phase

Audit installed Steam Repentance+, mod/runtime compatibility, Lua APIs, bridge
options, and training-profile isolation. REPENTOGON and game mods have not been
installed by this project: the audit determines the specific required components.
The game and user saves have not been changed.
