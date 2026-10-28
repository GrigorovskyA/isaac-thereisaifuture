# Evidence: pure-v8 first hour and observer frame timing

- Windows gate: 1271 passed with Lua, one existing synthetic All-NaN warning; strict OpenSpec 21/21; lint/format/mypy/pip clean.
- Native Windows/Steam Repentance+, file 2, seed 1, Python 3.12/RecurrentPPO; observation 5/action 2/reward pure-v8.
- Config SHA256: `fb22b3429127c22b325c20594d1ab6d2931fae684ceab6eef9af4731136eb938`. Fresh lineage; no reward-v7 checkpoint resumed.
- One-hour Start-Pure.cmd --initialize; 20,480,000,000-byte disk cap, max five consecutive faults, unlimited authorized death/stall restarts. stop.forever at 3600 seconds yields expected user_cancelled after cleanup.
- Source/deployed Lua and metadata hashes recorded in local preflight.json; old reward-v7 directory preserved with all file hashes and its stop marker.

## Native reward and timer checks

{
  "episodes": 62,
  "stalls": 47,
  "stall_idle_min": 40.0,
  "stall_idle_max": 40.203999999997905,
  "stagnation_min": -7.0,
  "audit_steps": 14110,
  "errors": []
}

## Observer frame timing

```text
windows            350  (3502.6 s of wall time)
updates/s          29.2
renders/s          59.9
snapshots/s        19.2
update callback    0.0% of wall time
render callback    1.6% of wall time
capture()          0.4% of wall time, 0.20 ms/snapshot
json.encode        0.8% of wall time, 0.41 ms/snapshot
```

## Bridge timing

{
  "rollouts": 27,
  "game_wait_share": 0.9053655254820716,
  "command_share": 0.0497594503470706,
  "python_share": 0.04487502417085787,
  "snapshots_per_step_mean": 4.321976273148148
}

Capture/encode are nested inside render callback time and must not be added to it. Bridge Python share is the residual of rollout wall time after game wait and commands. No timing enters policy inputs or rewards.

## Session and cleanup

{
  "started": 1793014540.163588,
  "config_hash": "fb22b3429127c22b325c20594d1ab6d2931fae684ceab6eef9af4731136eb938",
  "command": [
    "C:\\WINDOWS\\system32\\cmd.exe",
    "/d",
    "/c",
    "D:\\isaac\\Start-Pure.cmd",
    "C:\\Program Files (x86)\\Steam\\steamapps\\common\\The Binding of Isaac Rebirth",
    "C:\\Users\\Elmin\\Documents\\My Games\\Binding of Isaac Repentance+\\log.txt",
    "--initialize"
  ],
  "supervisor": {
    "stop_reason": "user cancelled",
    "consecutive_faults": 0,
    "sessions": [
      {
        "output": "D:\\isaac\\runs\\pure-v4\\supervisor\\session-20261026-123540-0001",
        "resumed": false,
        "parent": "",
        "latest": "fb22b342-s1-t13824",
        "state": "user_cancelled",
        "reason": "User cancellation requested"
      }
    ]
  },
  "attempts": [
    {
      "state": "user_cancelled",
      "updated_at": 1793018142.1276076,
      "observed_monotonic": 194525.046,
      "started_at": 1793014540.5522468,
      "deadline_monotonic": 219662.947753191,
      "elapsed_seconds": 3601.546000000002,
      "last_activity_monotonic": 194523.375,
      "phase_seconds": {
        "startup": 21.84299999999348,
        "waiting": 0.125,
        "training": 3563.265999999916,
        "checkpointing": 16.312000000092667
      },
      "latest_checkpoint": {
        "id": "fb22b342-s1-t13824",
        "steps": 13824,
        "path": "D:\\isaac\\runs\\pure-v4\\seed-1\\checkpoints\\fb22b342-s1-t13824",
        "completed_at": 1793018080.538043
      },
      "last_checkpoint_update_at": 1793018080.7131946,
      "checkpoint_note": null,
      "reason": "User cancellation requested",
      "stop_observed_monotonic": 194523.375,
      "fault": null,
      "learner_exit": 0,
      "cleanup_errors": [],
      "sampled_peak_bytes": 560584762,
      "ended_at": 1793018142.1276076
    }
  ],
  "latest": "fb22b342-s1-t13824",
  "state": "passed",
  "ended_at_utc": "2026-10-26T12:35:44.526773+00:00"
}

## Limits and continuation

Self-review only; reward accounting and timing are native qualification, not evidence of improved play. Both task 2.2 checkboxes are marked only if all checks pass. Reward-v8 task 2.3 remains open: new baseline sessions and later policy evaluation are required. Training is stopped after qualification; any continuation needs its newly authorized finite deadline. Raw audit, full game log, gate log and receipts remain under reports/local/pure-v8-one-hour-20261026 or runs/, outside Git.
