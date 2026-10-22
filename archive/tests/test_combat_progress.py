"""Synthetic endpoint/capture contracts; these tests do not verify native combat."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from test_combat_gate import Operator, World, snap
from test_combat_gate import clock as clock

from isaac_threrisaifuture.combat_gate import CombatGateEnv, GateConfig
from isaac_threrisaifuture.combat_progress import (
    CombatDiagnosticStop,
    CombatProgressMonitor,
    CombatTrace,
    policy_state,
    validate_limits,
)
from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.live import LiveRunOptions, make_live_env
from isaac_threrisaifuture.observation import ProtocolError
from isaac_threrisaifuture.session_runner import SessionPlan


def vector(snapshot):
    return encode(snapshot.entity_frame).vector


def pair(trace, before=None, after=None):
    before = before or snap(1, enemies={1: 10})
    after = after or snap(4, enemies={1: 9})
    return trace.transition(
        before,
        vector(before),
        after,
        vector(after),
        np.array([1, 2]),
        terminated=False,
        truncated=False,
        action_withheld=None,
    )


def test_separate_same_frame_policy_and_raw_endpoint_pair(tmp_path):
    trace = CombatTrace(tmp_path, 100_000)
    assert pair(trace)
    policy = json.loads(trace.policy_path.read_text())
    oracle = json.loads(trace.oracle_path.read_text())
    assert policy["record_id"] == oracle["record_id"] == 1
    assert policy["selected_action"] == [1, 2]
    for phase in ("before", "after"):
        from isaac_threrisaifuture.live import LiveSnapshot

        raw = LiveSnapshot.model_validate(oracle[phase])
        assert policy[phase] == policy_state(raw, vector(raw))
    assert '"oracle"' not in trace.policy_path.read_text()
    assert '"player_dead"' not in trace.policy_path.read_text()
    assert oracle["weapon_range"] is None
    assert oracle["weapon_range_status"] == "not_exported"
    assert trace.bytes_written == sum(
        p.stat().st_size for p in (trace.policy_path, trace.oracle_path)
    )
    old = trace.policy_path.read_bytes()
    with pytest.raises(FileExistsError):
        CombatTrace(tmp_path, 100_000)
    assert trace.policy_path.read_bytes() == old


def test_combined_byte_bound_at_exact_pair_boundary(tmp_path):
    probe = CombatTrace(tmp_path / "probe", 100_000)
    assert pair(probe)
    cap = probe.bytes_written
    small = CombatTrace(tmp_path / "small", cap - 1)
    assert not pair(small)
    assert small.bytes_written == 0
    assert small.policy_path.read_bytes() == small.oracle_path.read_bytes() == b""
    exact = CombatTrace(tmp_path / "exact", cap)
    assert pair(exact)
    assert not pair(exact)
    assert exact.records == 1 and exact.bytes_written == cap


def test_mismatched_vector_refused_before_writing(tmp_path):
    trace = CombatTrace(tmp_path, 100_000)
    before, after = snap(1), snap(4)
    bad = vector(before).copy()
    bad[0] += 0.1
    with pytest.raises(ProtocolError, match="does not match"):
        trace.transition(
            before,
            bad,
            after,
            vector(after),
            [0, 0],
            terminated=False,
            truncated=False,
            action_withheld=None,
        )
    assert trace.policy_path.stat().st_size == trace.oracle_path.stat().st_size == 0


def test_stagnation_accumulates_across_resets_without_counting_reset_gap():
    monitor = CombatProgressMonitor(6)
    first, second = snap(1, enemies={1: 10}), snap(4, enemies={1: 10})
    monitor.begin(first)
    assert not monitor.transition(first, second, eligible=True)
    baseline = snap(1000, enemies={1: 10})
    monitor.begin(baseline)
    assert monitor.updates_without_progress == 3
    assert monitor.transition(baseline, snap(1003, enemies={1: 10}), eligible=True)
    assert monitor.updates_without_progress == 6


def test_hp_floor_damage_but_not_healing_or_repeated_hp_loss_resets_window():
    monitor = CombatProgressMonitor(100)
    previous = snap(1, enemies={1: 10})
    monitor.begin(previous)
    for frame, hp, expected in [(4, 10, 3), (7, 8, 0), (10, 10, 3), (13, 8, 6)]:
        current = snap(frame, enemies={1: hp})
        monitor.transition(previous, current, eligible=True)
        assert monitor.updates_without_progress == expected
        previous = current
    # Software reset does not renew previously earned HP allowance.
    monitor.begin(snap(20, enemies={1: 10}))
    monitor.transition(snap(20, enemies={1: 10}), snap(23, enemies={1: 8}), eligible=True)
    assert monitor.updates_without_progress == 9
    monitor.transition(snap(23, enemies={1: 8}), snap(26, enemies={1: 7}), eligible=True)
    assert monitor.updates_without_progress == 0


def test_missing_enemy_overflow_and_phase_change_do_not_fake_progress():
    monitor = CombatProgressMonitor(100)
    previous = snap(1, enemies={1: 10})
    monitor.begin(previous)
    for current in [
        snap(4),
        snap(7, enemies={1: 5}),
        snap(10, enemies={1: 4}, overflow=1),
        snap(13, enemies={1: 3}),
    ]:
        monitor.transition(previous, current, eligible=True)
        previous = current
    assert monitor.updates_without_progress == 12
    phase = snap(16, enemies={1: 2})
    phase = phase.model_copy(
        update={
            "oracle": phase.oracle.model_copy(
                update={"enemies": [phase.oracle.enemies[0].model_copy(update={"max_hp": 20})]}
            )
        }
    )
    monitor.transition(previous, phase, eligible=True)
    assert monitor.updates_without_progress == 15


def test_room_change_clear_and_noncombat_spans():
    monitor = CombatProgressMonitor(100)
    first = snap(1, enemies={1: 10})
    monitor.begin(first)
    second = snap(31, enemies={1: 10})
    monitor.transition(first, second, eligible=False)
    assert monitor.updates_without_progress == 0
    monitor.transition(second, snap(34, enemies={1: 10}), eligible=True)
    monitor.transition(snap(34, enemies={1: 10}), snap(37, clear=True), eligible=True)
    assert monitor.updates_without_progress == 0
    monitor.transition(snap(37, clear=True), snap(40, visit=2, enemies={1: 10}), eligible=True)
    assert monitor.updates_without_progress == 0
    monitor.transition(
        snap(40, visit=2, enemies={1: 10}), snap(43, visit=2, enemies={1: 10}), eligible=True
    )
    assert monitor.updates_without_progress == 3


@pytest.mark.parametrize(
    "trace,window",
    [(-1, None), (True, None), (268435457, None), (0, 0), (0, True), (0, 108001), (0, 1.5)],
)
def test_invalid_limits_refused(trace, window, tmp_path):
    with pytest.raises(ValueError):
        validate_limits(trace, window)
    with pytest.raises(ValueError):
        LiveRunOptions(
            "random",
            tmp_path,
            combat_gate=True,
            combat_trace_bytes=trace,
            combat_progress_updates=window,
        )


@pytest.mark.parametrize("options", [{"combat_trace_bytes": 100}, {"combat_progress_updates": 10}])
def test_diagnostics_require_gate(tmp_path, options):
    with pytest.raises(ValueError, match="require the combat gate"):
        LiveRunOptions("random", tmp_path, **options)


def make_gate(tmp_path, *, trace=0, window=None):
    world = World(operator=Operator(tmp_path, navigate=False))
    world.enemies = {1: 10}
    records = []
    gate = CombatGateEnv(
        make_live_env(world, max_faults=0),
        GateConfig(
            tmp_path / "combat_gate",
            wait_cap_seconds=5,
            poll_seconds=0.05,
            combat_trace_bytes=trace,
            combat_progress_updates=window,
        ),
        record=lambda *row: records.append(row),
    )
    return world, gate, records


@pytest.mark.parametrize("next_call", ["step", "reset"])
def test_pending_progress_stop_preserves_real_step_then_releases_before_next_action(
    tmp_path,
    clock,
    next_call,
):
    world, gate, records = make_gate(tmp_path, window=3, trace=100_000)
    initial, initial_info = gate.reset()
    result = gate.step(np.array([1, 2]))
    assert result[2:4] == (False, False)
    assert gate.stats.combat_steps == 1
    assert world.actions == 1
    with pytest.raises(CombatDiagnosticStop, match="registered-progress window"):
        gate.step([1, 2]) if next_call == "step" else gate.reset()
    assert world.actions == 1 and world.commands[-1][0] == "release"
    assert gate.state == "stopped" and not gate.stats.outcomes
    assert "oracle" not in result[4] and "oracle" not in initial_info
    np.testing.assert_array_equal(initial, vector(snap(3, enemies={1: 10})))
    policy = json.loads((tmp_path / "combat_gate/diagnostics/policy.jsonl").read_text())
    assert policy["selected_action"] == [1, 2]
    assert any(row[1]["event"] == "diagnostic_stop_pending" for row in records)
    gate.close()


def test_trace_exhaustion_stops_cleanly_without_exceeding_cap(tmp_path, clock):
    world, gate, _ = make_gate(tmp_path, trace=1)
    gate.reset()
    result = gate.step([0, 0])
    assert result[2:4] == (False, False)
    with pytest.raises(CombatDiagnosticStop, match="byte limit"):
        gate.step([0, 0])
    assert world.actions == gate.stats.combat_steps == 1
    assert not gate.stats.outcomes
    assert sum(p.stat().st_size for p in (tmp_path / "combat_gate/diagnostics").iterdir()) == 0
    gate.close()


def test_real_software_episode_reset_does_not_renew_progress_window(tmp_path, clock):
    world, gate, _ = make_gate(tmp_path, window=6)
    base = gate.env.unwrapped
    base.scenarios = (replace(base.scenarios[0], max_game_updates=3),)
    gate.reset()
    first = gate.step([0, 0])
    assert first[3] and first[4]["outcome"] == "unknown"
    gate.reset()
    second = gate.step([0, 0])
    assert second[3] and second[4]["outcome"] == "unknown"
    with pytest.raises(CombatDiagnosticStop, match="6 game updates"):
        gate.reset()
    assert world.actions == gate.stats.combat_steps == 2
    assert gate.stats.outcomes == {"unknown": 2}
    gate.close()


def test_live_option_factory_passes_explicit_limits(tmp_path, clock):
    from isaac_threrisaifuture.live import _gated

    world = World(operator=Operator(tmp_path, navigate=False))
    world.enemies = {1: 10}
    options = LiveRunOptions(
        "random", tmp_path, combat_gate=True, combat_trace_bytes=100_000, combat_progress_updates=3
    )
    gate = _gated(make_live_env(world), options, lambda *args: None, tmp_path, clock.now + 100)
    gate.reset()
    gate.step([0, 0])
    with pytest.raises(CombatDiagnosticStop, match="registered-progress"):
        gate.step([0, 0])
    assert (tmp_path / "combat_gate/diagnostics/policy.jsonl").is_file()
    gate.close()


def test_training_stop_reports_unsaved_real_decision_without_new_checkpoint(tmp_path):
    import yaml
    from test_checkpoint_policy import RAW_CONFIG

    from isaac_threrisaifuture.live import _train_run

    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(RAW_CONFIG), encoding="utf-8")
    world = World(operator=Operator(tmp_path, navigate=False))
    world.enemies = {1: 10}
    records = []
    options = LiveRunOptions(
        "train",
        tmp_path / "out",
        minutes=0.2,
        steps=32,
        config_path=config,
        combat_gate=True,
        gate_wait_minutes=0.01,
        combat_progress_updates=3,
    )
    _train_run(world, options, lambda *row: records.append(row), lambda event: None, tmp_path)
    assert records[-2][0] == "budget" and "registered-progress" in records[-2][1]
    accounting = records[-1][1]
    assert accounting["combat_decisions"] == accounting["unsaved_steps"] == 1
    assert accounting["checkpointed_timesteps"] == 0
    assert not list((tmp_path / "out").rglob("latest.txt"))
    assert world.closed and world.commands[-1][0] == "release"


def test_session_worker_passes_declared_limits(tmp_path, monkeypatch):
    from isaac_threrisaifuture import session_runner as runner

    payload = {
        "options": {
            "output": str(tmp_path),
            "run_root": str(tmp_path / "run"),
            "config": str(tmp_path / "config"),
            "seed": 20,
            "steps": 1000,
            "seconds": 120,
            "navigation_scale": 1,
            "navigation_time_dominant": True,
            "combat_trace_bytes": 100_000,
            "combat_progress_updates": 1800,
        },
        "clock": {"deadline": runner.time.monotonic() + 120},
    }
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(payload), encoding="utf-8")
    captured = []
    monkeypatch.setattr(runner, "run_live", lambda options, **kwargs: captured.append(options))
    runner.worker(plan)
    assert captured[0].combat_trace_bytes == 100_000
    assert captured[0].combat_progress_updates == 1800
    assert captured[0].resume and captured[0].seed == 20


def test_session_plan_records_limits_without_mutating_training_contract(tmp_path):
    plan = SessionPlan(
        *(Path(tmp_path / name) for name in ("game", "log", "cfg", "root", "out")),
        "parent",
        20,
        120,
        1000,
        2,
        10**7,
        combat_trace_bytes=100_000,
        combat_progress_updates=1800,
    )
    assert plan.combat_trace_bytes == 100_000 and plan.combat_progress_updates == 1800
    with pytest.raises(ValueError):
        replace(plan, combat_progress_updates=0)
