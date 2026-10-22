# Evidence: screenless-steam-launch

- Date: 2026-10-20, Europe/Amsterdam.
- Revision: b973a2c, dirty checkout with prior unrelated work preserved.
- Scope: Steam URI startup and bounded terminal readiness, no desktop input/capture.
- Environment: native Windows, Python3.12 project venv, installed Repentance+ and
  approved observer. No dependencies or observer deployment changed by this task.
- No training, model migration, fresh lineage, approval or restart was requested.

## Results

| Check | Exit | Status | Evidence |
|---|---|---|---|
| Launcher pytest | 0 | passed:27,zero skipped | reports/local/screenless-targeted.txt |
| Check.ps1 | 0 | passed:1952 tests in49.44s,Ruff/format/mypy/pip,OpenSpec34/34 | reports/local/screenless-check.txt |
| Frozen Python/PS source hashes | n/a | passed before/after/current | reports/local/screenless-before.json,screenless-after.json |
| PowerShell parser/preflight-only in current host | 0 | passed,no launch | primary command output |
| Windows PowerShell5.1 wrapper launch | 1 | blocked by execution policy before launch | reports/local/screenless-native.txt |
| Direct CMD Steam startup | 2 | launch observed; readiness blocked by no Lua peer | reports/local/screenless-cmd-native.txt,screenless-cmd-result.json |
| Successful native first snapshot | n/a | not_run | manual Continue unavailable during bounded attempt |

Luna ran only offline checks; primary verified actual pytest count (1952),rather
than mistaking OpenSpec's34 items for the pytest total. The source hashes match.
Full gate took56 seconds. Output logs were small, but the assigned20MiB disk cap
did not cover actual pytest temporary output:86,104,567 newly written bytes in593
files after the before record. Total retained temp storage172,200,881 bytes.
Budget compliance failed; no rerun or temporary-file deletion was performed.
This does not convert failed budget compliance into a passing check.

## Real game

First PS5.1 invocation failed before launch. No execution policy or Windows setting
was changed. The new CMD entry invokes the same project Python directly, following
the existing repository CMD entry-point pattern. Separate finite plan recorded
before use: one snapshot,20s configured duration/connection limit,45s outer wall
budget,4MiB logs,zero input/screenshots/training/death/restart/retry. The launcher's
accept wait is capped at half the remaining deadline,so this attempt failed after
about10s without a peer. CMD propagated Python exit2 without a terminal pause.

Steam request emitted after listener readiness; primary verified new PID47644 at
15:10:58+02:00 with the expected installed isaac-ng.exe path. No visual menu state
is inferred from a process alone. No handshake/snapshot was received,so no ready
claim is accepted. Listener count zero after exit; game count one, intentionally
left open for normal manual entry/exit per launcher contract. No gameplay input
or training was sent. No approval or checkpoint writes were made.

## Primary self-review and OpenSpec verification

Using openspec-verify-change for screenless-steam-launch. This is primary
self-review,not independent review. Completeness3/4: native handshake task2.2 is
incomplete and blocks archive. Both requirements map to launcher lifecycle and
CMD/PS wrappers. Offline scenarios cover port/instance/hash refusal,listener before
launch,Steam dispatch error,first snapshot versus handshake-only,deadlines and
resource cleanup. Existing launcher schema/protocol is unchanged. The CMD wrapper
was added after the full gate; it changes no Python/test source and its native
failure/exit propagation was exercised separately. PS parser and local preflight
passed,while PS5.1 policy refusal is retained as a distinct failure.

No keys,screen APIs,new mods,Steam options,Cloud or saves are edited. Readiness
explicitly marks save_slot_verified=false. The URI requests app250900; preflight
does not itself force Steam's eventual installation path. Actual path verified in
this attempt. A successful bridge handshake still would not prove slot identity.
No other implementation/design discrepancy found. Native scenario coverage remains
incomplete; no archive or fully autonomous startup acceptance.

## Limitations and next action

The installed bridge has no verified direct file2/Continue API. REPENTOGON has
[separate menu callbacks](https://repentogon.com/enums/ModCallbacks.html) and
[menu selection methods](https://repentogon.com/menus/SaveMenu.html),but selection
alone does not prove slot loading. It is uninstalled and its
[version/runtime requirements](https://repentogon.com/install.html) need a separate
compatibility audit and installation authorization. No extension was installed.

User clarification is pending: whether a local script may send menu-only keys,
without any agent desktop tool or screenshots. Until answered,no such input is
implemented or sent. Otherwise manual file2/Continue remains necessary. Next
acceptance check is one validated native snapshot after entry. Training additionally
requires explicit reward-contract lineage handling; t8960 is not silently resumed
under the new conservative reward contract.
