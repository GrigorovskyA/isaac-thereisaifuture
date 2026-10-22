## Why

Agent startup currently relies on costly desktop screenshots and guarded menu input.
The read-only launcher also bypasses Steam when starting the executable. Provide a
small terminal entry point with structured readiness and no desktop interaction.

## What Changes

- Launch through Steam's existing application URI, preserving launch options.
- Add a noninteractive agent script that waits for one validated bridge snapshot.
- Distinguish launch requested, waiting for manual file-2 entry, and bridge ready.
- Document the remaining automatic Continue blocker rather than injecting keys.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `observation-launcher`: Steam launch and short agent readiness entry point.

## Impact

Python launcher, CMD/PowerShell wrappers, launcher tests and documentation. No new
dependency, game deployment, save change, training or menu automation. Acceptance
requires offline lifecycle tests and a separate bounded native launch check.
