#!/usr/bin/env bash
# POSIX (macOS/Linux) pre-check mirroring scripts/Check.ps1. Windows Check.ps1 stays the
# authoritative gate: this run uses a non-game JSON shim and type-checks as win32.
# Environment: ISAAC_PY (python with deps + lupa), ISAAC_JSON_LUA (json.lua for Lua tests),
# ISAAC_OPENSPEC (openspec.js path; node_modules on SMB shares may be unreadable).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
py="${ISAAC_PY:-$HOME/.venvs/isaac/bin/python}"
openspec="${ISAAC_OPENSPEC:-$HOME/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js}"
cache="${XDG_CACHE_HOME:-$HOME/.cache}"
cd "$root"
[ -n "${ISAAC_JSON_LUA:-}" ] || echo "ISAAC_JSON_LUA unset: Lua observer suites will skip" >&2
"$py" -m ruff check --no-cache src tests scripts/smoke_rl.py scripts/compare_eval.py
"$py" -m ruff format --no-cache --check src tests scripts/smoke_rl.py scripts/compare_eval.py
"$py" -m mypy --platform win32 --cache-dir "$cache/isaac-mypy"
"$py" -m pytest -p no:cacheprovider -m "not game"
uv pip check --python "$py"
XDG_CONFIG_HOME="$root/.tooling" OPENSPEC_TELEMETRY=0 node "$openspec" validate --all --strict
echo "POSIX pre-check passed. Run scripts/Check.ps1 on Windows; no real-game check ran."
