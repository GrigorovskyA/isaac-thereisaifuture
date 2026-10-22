"""Offline management routing over the actual live gate/backend/environment stack."""

import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import ValidationError
from test_combat_gate import FakeClock, World, snap

from isaac_threrisaifuture.combat_gate import GateConfig
from isaac_threrisaifuture.combat_navigation import (
    CombatNavigationGate,
    NavigationStopped,
    pulse_direction,
)
from isaac_threrisaifuture.live import LiveRunOptions, make_live_env
from isaac_threrisaifuture.navigation_wire import NavigationFrame
from isaac_threrisaifuture.observer_client import ObserverConfig


def telemetry(**changes):
    return NavigationFrame.model_validate(
        {
            "version": 2,
            "stage": 1,
            "stage_type": 0,
            "room_type": 1,
            "room_index": 4,
            "shape": 1,
            "doors": [{"slot": 2, "position": {"x": 600.0, "y": 200.0}}],
            "grid": {
                "origin": {"x": 0.0, "y": 0.0},
                "spacing": 40,
                "width": 17,
                "height": 12,
                "walkable": "1" * (17 * 12),
            },
            **changes,
        }
    )


def navigable(sample=None, **changes):
    sample = sample or snap(10, clear=True)
    return sample.model_copy(
        update={"oracle": sample.oracle.model_copy(update={"navigation": telemetry(**changes)})}
    )


def gate_for(world, tmp_path):
    return CombatNavigationGate(
        make_live_env(world, max_faults=0), GateConfig(tmp_path / "combat_gate", wait_cap_seconds=5)
    )


def time_gate(world, tmp_path, deadline=None, record=None):
    return CombatNavigationGate(
        make_live_env(world, max_faults=0),
        GateConfig(tmp_path / "combat_gate", wait_cap_seconds=60),
        run_deadline=deadline or time.monotonic() + 60,
        time_dominant=True,
        record=record,
    )


class LongTravelWorld(World):
    def snapshot(self):
        return navigable(World.snapshot(self), room_index=self.visit)

    def command(self, kind, reference, **kwargs):
        result = World.command(self, kind, reference, **kwargs)
        if kind == "action" and not reference.oracle.enemies:
            self.enter_room({100: 10} if self.visit >= 25 else {})
        return result


def test_time_mode_crosses_more_than_twenty_rooms_without_learning_travel(tmp_path):
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    world = LongTravelWorld()
    world.clear = True
    gate = time_gate(world, tmp_path)
    # These cumulative counters are telemetry only, even beyond the old scale-5 caps.
    gate.nav_commands, gate.nav_seconds, gate.nav_transitions = 2000, 1000, 30
    venv = VecNormalize(DummyVecEnv([lambda: gate]), norm_reward=False)
    try:
        venv.reset()
        assert world.visit == 26 and gate.nav_transitions == 55
        assert gate.stats.accepted == 1 and gate.stats.combat_steps == 0
        assert venv.obs_rms.count == pytest.approx(1.0001)
        venv.step(np.array([[1, 2]]))
        assert gate.stats.combat_steps == 1
        assert venv.obs_rms.count == pytest.approx(2.0001)
        assert len(gate._routes.edges) == 25
    finally:
        venv.close()


class CycleWorld(World):
    def snapshot(self):
        return navigable(World.snapshot(self), room_index=1 if self.visit % 2 else 2)

    def command(self, kind, reference, **kwargs):
        result = World.command(self, kind, reference, **kwargs)
        if kind == "action":
            self.enter_room({})
        return result


def test_time_mode_stops_observed_empty_cycle_and_reports_search(tmp_path):
    world = CycleWorld()
    world.clear = True
    records = []
    gate = time_gate(world, tmp_path, record=lambda *item: records.append(item))
    try:
        with pytest.raises(NavigationStopped, match="Observed ordinary-room component exhausted"):
            gate.reset()
        assert world.visit == 3 and gate.nav_transitions == 2
        assert gate.stats.combat_steps == 0 and gate.stats.accepted == 0
        assert gate.state == "stopped" and world.commands[-1][0] == "release"
        assert any(item[1].get("event") == "navigation_no_progress" for item in records)
    finally:
        gate.close()


@pytest.mark.parametrize("changes", [{"game_epoch": 2}, {"session_id": "b" * 32}])
def test_observed_routes_reset_with_instance_identity(tmp_path, changes):
    gate = time_gate(World(), tmp_path)
    try:
        sample = navigable()
        gate._remember(sample)
        gate._routes.connect(4, 2, 6)
        gate._remember(sample.model_copy(update=changes))
        assert not gate._routes.edges
        assert gate._routes.doors == {4: (2,)}
    finally:
        gate.close()


def test_observed_routes_reset_with_floor_identity(tmp_path):
    gate = time_gate(World(), tmp_path)
    try:
        gate._remember(navigable())
        gate._routes.connect(4, 2, 6)
        gate._remember(navigable(stage=2))
        assert not gate._routes.edges
    finally:
        gate.close()


def test_time_mode_preserves_global_expiry_health_and_release_guards(tmp_path):
    world = World()
    gate = time_gate(world, tmp_path, deadline=time.monotonic() - 1)
    sample = navigable()
    try:
        with pytest.raises(Exception, match="budget|expired"):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
        assert not world.commands
        gate.run_deadline = time.monotonic() + 10
        damaged = sample.model_copy(
            update={
                "player": sample.player.model_copy(
                    update={
                        "health": sample.player.health.model_copy(update={"red_half_hearts": 0}),
                    }
                )
            }
        )
        gate.backend.poll = lambda _: (damaged, 1)
        with pytest.raises(NavigationStopped, match="Health changed"):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
        assert [kind for kind, _ in world.commands] == ["action", "release"]
    finally:
        gate.close()


def test_time_mode_requires_finite_deadline_and_explicit_unscaled_auto_mode(tmp_path):
    for changes in (
        {},
        {"run_deadline": float("inf")},
        {"run_deadline": time.monotonic() + 10, "budget_scale": 2},
    ):
        with pytest.raises(ValueError, match="finite"):
            CombatNavigationGate(
                make_live_env(World(), max_faults=0),
                GateConfig(tmp_path / "unused"),
                time_dominant=True,
                **changes,
            )
    for changes in ({}, {"auto_navigate": True, "combat_gate": True, "navigation_budget_scale": 2}):
        with pytest.raises(ValueError, match="Time-dominant"):
            LiveRunOptions("train", tmp_path, navigation_time_dominant=True, **changes)


def test_time_mode_handoff_uses_session_window_not_diagnostic_wait_cap(tmp_path):
    from isaac_threrisaifuture.live import _gated

    options = LiveRunOptions(
        "train",
        tmp_path,
        minutes=0.1,
        combat_gate=True,
        auto_navigate=True,
        navigation_time_dominant=True,
    )
    deadline = time.monotonic() + 6
    gate = _gated(
        make_live_env(World(), max_faults=0), options, lambda *args: None, tmp_path, deadline
    )
    try:
        assert gate.config.wait_cap_seconds == 6
        assert gate.run_deadline == deadline and gate.time_dominant
    finally:
        gate.close()


def test_missing_action_ack_cannot_establish_a_confirmed_route(tmp_path):
    from isaac_threrisaifuture.observation import BridgeTimeout

    world = World()
    gate = time_gate(world, tmp_path)
    sample = navigable()
    destination = navigable(snap(100, visit=2, clear=True), room_index=6)
    gate.backend.poll = lambda _: (destination, 1)

    def command(kind, reference, **kwargs):
        if kind == "action":
            raise BridgeTimeout("Missing action acknowledgement")
        return SimpleNamespace(status="rejected", frame_id=10)

    world.command = command
    try:
        with pytest.raises(BridgeTimeout, match="Missing action acknowledgement"):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
        assert not gate._routes.edges
        assert gate.stats.combat_steps == 0
    finally:
        gate.close()


class NavigationWorld(World):
    def snapshot(self):
        return navigable(super().snapshot(), room_index=self.visit)

    def command(self, kind, reference, **kwargs):
        result = super().command(kind, reference, **kwargs)
        if kind == "action" and not reference.oracle.enemies:
            assert kwargs["shoot"] == "none" and kwargs["frames"] <= 6
            self.enter_room({100 + self.visit: 10})
        return result


def test_multi_fight_navigation_excluded_from_normalizer_samples(tmp_path):
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    world = NavigationWorld(fight_len=3)
    world.clear = True
    gate = gate_for(world, tmp_path)
    venv = VecNormalize(DummyVecEnv([lambda: gate]), norm_reward=False)
    try:
        venv.reset()
        initial = venv.obs_rms.count
        assert gate.nav_commands == 2 and gate.stats.combat_steps == 0
        for _ in range(6):
            venv.step(np.array([[1, 2]]))
        assert gate.stats.combat_steps == 6 and gate.nav_commands >= 6
        assert gate.stats.handoffs >= 3 and world.visit >= 4
        assert gate.nav_transitions == world.visit - 1
        assert venv.obs_rms.count == pytest.approx(initial + 6)
        assert not gate.cleanup_errors
    finally:
        venv.close()


def test_routing_prefers_unused_exits_and_resets_epoch_memory(tmp_path):
    gate = gate_for(World(), tmp_path)
    sample = navigable(doors=[{"slot": i, "position": {"x": 120.0, "y": 200.0}} for i in (0, 2)])
    try:
        assert [gate._choose(sample).slot for _ in range(3)] == [0, 2, 0]
        sample = sample.model_copy(update={"game_epoch": 2})
        assert gate._choose(sample).slot == 0
    finally:
        gate.close()


def test_unreachable_exit_is_skipped_without_a_direct_move(tmp_path):
    gate = gate_for(World(), tmp_path)
    sample = navigable(
        doors=[
            {"slot": 0, "position": {"x": 0.0, "y": 200.0}},
            {"slot": 2, "position": {"x": 600.0, "y": 200.0}},
        ]
    )
    nav = sample.oracle.navigation
    grid = nav.grid
    mask = list(grid.walkable)
    mask[5 * grid.width + 1] = "0"
    nav = nav.model_copy(update={"grid": grid.model_copy(update={"walkable": "".join(mask)})})
    sample = sample.model_copy(
        update={"oracle": sample.oracle.model_copy(update={"navigation": nav})}
    )
    try:
        assert gate._choose(sample).slot == 2
    finally:
        gate.close()


@pytest.mark.parametrize("changes", [{"version": 1, "grid": None}, {"room_type": 5}, {"doors": []}])
def test_unsupported_geometry_or_no_exit_sends_no_action(tmp_path, changes):
    world = World()
    gate = gate_for(world, tmp_path)
    try:
        with pytest.raises(NavigationStopped):
            gate._choose(navigable(**changes))
        assert not world.commands
    finally:
        gate.close()


@pytest.mark.parametrize("budget", ["nav_commands", "nav_seconds", "nav_transitions"])
def test_navigation_budgets_do_not_send_another_action(tmp_path, budget):
    world = World()
    gate = gate_for(world, tmp_path)
    setattr(gate, budget, {"nav_commands": 256, "nav_seconds": 90, "nav_transitions": 4}[budget])
    sample = navigable()
    try:
        with pytest.raises(NavigationStopped, match="budget"):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
        assert not world.commands
    finally:
        gate.close()


def test_health_change_releases_and_stops_without_sample(tmp_path):
    world = World()
    gate = gate_for(world, tmp_path)
    sample = navigable()
    damaged = sample.model_copy(
        update={
            "player": sample.player.model_copy(
                update={"health": sample.player.health.model_copy(update={"red_half_hearts": 0})}
            )
        }
    )
    gate.backend.poll = lambda timeout: (damaged, 1)
    try:
        with pytest.raises(NavigationStopped, match="Health changed"):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
        assert [kind for kind, _ in world.commands] == ["action", "release"]
        assert gate.stats.combat_steps == 0
    finally:
        gate.close()


def test_same_room_release_rejection_is_explicit_stop(tmp_path):
    world = World()
    gate = gate_for(world, tmp_path)
    sample = navigable()
    gate.backend.poll = lambda timeout: (sample.model_copy(update={"frame_id": 100}), 1)
    world.command = lambda *a, **kw: SimpleNamespace(
        status="rejected" if a[0] == "release" else "accepted", frame_id=10
    )
    try:
        with pytest.raises(NavigationStopped, match="release rejected"):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
    finally:
        gate.close()


@pytest.mark.parametrize("foreign", [False, True])
def test_delayed_transition_after_rejected_release_requires_same_epoch(tmp_path, foreign):
    world = World()
    gate = gate_for(world, tmp_path)
    sample = navigable()
    destination = navigable(snap(100, visit=2, epoch=2 if foreign else 1, clear=True))
    polls = iter([sample.model_copy(update={"frame_id": 100}), destination])
    gate.backend.poll = lambda timeout: (next(polls), 1)
    calls = []

    def command(kind, reference, **kwargs):
        calls.append(kind)
        return SimpleNamespace(status="rejected" if kind == "release" else "accepted", frame_id=10)

    world.command = command
    try:
        if foreign:
            with pytest.raises(NavigationStopped, match="epoch changed"):
                gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
        else:
            result = gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
            assert result.room.visit_id == 2
        assert calls == ["action", "release"]
        assert gate.stats.combat_steps == 0
    finally:
        gate.close()


def test_transport_bounds_and_explicit_mode():
    for changes in (
        {"version": True},
        {"version": "1"},
        {"shape": 13},
        {"room_index": -1},
        {"doors": [{"slot": 2, "position": {"x": float("nan"), "y": 0.0}}]},
        {"doors": [{"slot": 2, "position": {"x": 1.0, "y": 1.0}}] * 2},
    ):
        with pytest.raises(ValidationError):
            telemetry(**changes)
    with pytest.raises(ValueError):
        ObserverConfig(combat_navigation=True)
    with pytest.raises(ValueError):
        LiveRunOptions(mode="random", out_dir=Path("unused"), auto_navigate=True)
    assert not ObserverConfig().combat_navigation
    assert not LiveRunOptions(mode="random", out_dir=Path("unused")).auto_navigate


def test_direction_uses_measured_alignment_not_fixed_room_center():
    sample = navigable()
    door = sample.oracle.navigation.doors[0]
    direction, frames = pulse_direction(sample, door)
    assert direction in ("left", "up", "right", "down") and 1 <= frames <= 6


def test_stationary_pulses_stop_and_cleanup_without_learning(tmp_path):
    world = World()
    world.clear = True
    original = world.snapshot
    world.snapshot = lambda: navigable(original())
    gate = gate_for(world, tmp_path)
    try:
        with pytest.raises(NavigationStopped, match="stationary"):
            gate.reset()
        assert gate.nav_commands == 6 and gate.stats.combat_steps == 0
        assert gate.state == "stopped" and not gate.cleanup_errors
        assert world.commands[-1][0] == "release"
    finally:
        gate.close()


def test_active_policy_and_expired_deadline_cannot_navigate(tmp_path):
    world = World()
    gate = gate_for(world, tmp_path)
    sample = navigable()
    try:
        gate.env.unwrapped.controller._running = True
        with pytest.raises(RuntimeError):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
        gate.env.unwrapped.controller._running = False
        with pytest.raises(Exception, match="expired"):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() - 1)
        assert not world.commands
    finally:
        gate.close()


def test_frozen_render_frames_wait_without_navigation_or_readiness(tmp_path):
    world = World()
    world.clear = True
    frozen = navigable(world.snapshot())
    world.snapshot = lambda: frozen
    gate = CombatNavigationGate(
        make_live_env(world, max_faults=0),
        GateConfig(tmp_path / "combat_gate", wait_cap_seconds=0.05, poll_seconds=0.01),
    )
    try:
        with pytest.raises(Exception, match="expired"):
            gate.reset()
        assert not any(kind == "action" for kind, _ in world.commands)
        assert gate.stats.accepted == 0
    finally:
        gate.close()


def test_short_pulse_timeout_does_not_claim_original_handoff_expired(tmp_path):
    from isaac_threrisaifuture.combat_gate import CombatGateExpired

    world = World()
    gate = gate_for(world, tmp_path)
    sample = navigable()

    def expired(_timeout):
        raise CombatGateExpired("short pulse cap")

    gate.backend.poll = expired
    try:
        with pytest.raises(NavigationStopped, match="pulse deadline"):
            gate._pulse(sample, sample.oracle.navigation.doors[0], time.monotonic() + 5)
        assert [kind for kind, _ in world.commands] == ["action", "release"]
    finally:
        gate.close()


@pytest.fixture
def exit_clock(monkeypatch):
    from isaac_threrisaifuture import combat_gate, combat_navigation, live

    clock = FakeClock()
    for module in (combat_gate, combat_navigation, live):
        monkeypatch.setattr(module, "time", clock)
    return clock


class ExitSettlingWorld(NavigationWorld):
    def __init__(self, clock, *, resolution="open", after=15):
        super().__init__()
        self.clock, self.resolution, self.after = clock, resolution, after

    def snapshot(self):
        if self.visit == 1 and self.resolution == "clear_before_open" and self.frame >= 8:
            self.clear = True
        if self.visit == 1 and self.frame >= self.after:
            if self.resolution in ("open", "clear_before_open"):
                self.clear = True
            elif self.resolution == "combat":
                self.enemies = {20: 10}
        sample = super().snapshot()
        if self.visit == 1 and (
            not self.clear or (self.resolution == "clear_before_open" and self.frame < self.after)
        ):
            sample = navigable(sample, room_index=self.visit, doors=[])
            if self.frame >= 8:
                if self.resolution == "health":
                    health = sample.player.health.model_copy(
                        update={"red_half_hearts": sample.player.health.red_half_hearts - 1}
                    )
                    sample = sample.model_copy(
                        update={"player": sample.player.model_copy(update={"health": health})}
                    )
                elif self.resolution in ("paused", "frozen"):
                    sample = sample.model_copy(
                        update={
                            "status": "paused" if self.resolution == "paused" else "active",
                            "frame_id": 8,
                        }
                    )
        return sample


@pytest.mark.parametrize("resolution", ["open", "clear_before_open"])
def test_delayed_native_door_opening_waits_without_normalizer_samples(
    tmp_path, exit_clock, resolution
):
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    world = ExitSettlingWorld(exit_clock, resolution=resolution)
    gate = gate_for(world, tmp_path)
    venv = VecNormalize(DummyVecEnv([lambda: gate]), norm_reward=False)
    try:
        venv.reset()
        assert world.visit == 2 and gate.stats.accepted == 1
        assert min(frame for kind, frame in world.commands if kind == "action") >= 15
        assert gate.nav_commands == 2 and gate.stats.combat_steps == 0
        assert venv.obs_rms.count == pytest.approx(1.0001)  # reset only, never waiting frames
        assert not gate.cleanup_errors
    finally:
        venv.close()


def test_combat_return_during_exit_wait_requires_fresh_readiness(tmp_path, exit_clock):
    world = ExitSettlingWorld(exit_clock, resolution="combat")
    gate = gate_for(world, tmp_path)
    try:
        gate.reset()
        assert gate.stats.accepted == 1 and gate.state == "combat_active"
        assert world.frame >= 15 and gate.nav_commands == 0
        assert not any(kind == "action" for kind, _ in world.commands)
        assert gate.stats.combat_steps == 0
    finally:
        gate.close()


@pytest.mark.parametrize("resolution", ["never", "paused", "frozen"])
def test_exit_wait_stops_in_two_seconds_without_renewal(tmp_path, exit_clock, resolution):
    world = ExitSettlingWorld(exit_clock, resolution=resolution)
    gate = gate_for(world, tmp_path)
    started = exit_clock.now
    try:
        with pytest.raises(NavigationStopped, match="after settling wait"):
            gate.reset()
        assert 2 <= exit_clock.now - started <= 2.5
        assert not any(kind == "action" for kind, _ in world.commands)
        assert gate.stats.accepted == gate.stats.combat_steps == gate.nav_commands == 0
        assert not gate.cleanup_errors
    finally:
        gate.close()


def test_health_change_during_exit_wait_stops_before_input(tmp_path, exit_clock):
    world = ExitSettlingWorld(exit_clock, resolution="health")
    gate = gate_for(world, tmp_path)
    try:
        with pytest.raises(NavigationStopped, match="Health changed while waiting"):
            gate.reset()
        assert not any(kind == "action" for kind, _ in world.commands)
        assert gate.stats.accepted == gate.nav_commands == 0
    finally:
        gate.close()


def test_exit_settling_cannot_extend_original_gate_cap(tmp_path, exit_clock):
    from isaac_threrisaifuture.combat_gate import CombatGateExpired

    world = ExitSettlingWorld(exit_clock, resolution="never")
    gate = CombatNavigationGate(
        make_live_env(world, max_faults=0),
        GateConfig(tmp_path / "combat_gate", wait_cap_seconds=0.5),
    )
    started = exit_clock.now
    try:
        with pytest.raises(CombatGateExpired):
            gate.reset()
        assert exit_clock.now - started <= 0.6
        assert not any(kind == "action" for kind, _ in world.commands)
    finally:
        gate.close()


def test_cleared_room_without_ordinary_exits_still_stops_immediately(tmp_path, exit_clock):
    world = ExitSettlingWorld(exit_clock, resolution="never")
    world.snapshot = lambda: navigable(snap(world.frame, clear=True), doors=[])
    gate = gate_for(world, tmp_path)
    started = exit_clock.now
    try:
        with pytest.raises(NavigationStopped, match="No open ordinary-room exit"):
            gate.reset()
        assert exit_clock.now - started < 0.5
        assert gate.nav_commands == 0
    finally:
        gate.close()


def test_scaled_navigation_can_cross_more_than_four_rooms_without_extra_samples(tmp_path):
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    world = NavigationWorld(fight_len=1)
    world.clear = True
    gate = CombatNavigationGate(
        make_live_env(world, max_faults=0), GateConfig(tmp_path / "combat_gate"), budget_scale=5
    )
    venv = VecNormalize(DummyVecEnv([lambda: gate]), norm_reward=False)
    try:
        venv.reset()
        count = venv.obs_rms.count
        for _ in range(8):
            venv.step(np.array([[1, 2]]))
        assert 4 < gate.nav_transitions <= 20
        assert gate.nav_commands <= 1280 and gate.nav_seconds <= 450
        assert gate.stats.combat_steps == 8
        # VecEnv substitutes reset observations inside steps; waiting polls add none.
        assert venv.obs_rms.count == pytest.approx(count + 8)
    finally:
        venv.close()


def test_five_observed_deaths_stop_before_another_reset(tmp_path, exit_clock):
    from isaac_threrisaifuture.live import LiveBudgetExpired

    class DeathEachFight(NavigationWorld):
        def command(self, kind, reference, **kwargs):
            result = super().command(kind, reference, **kwargs)
            if kind == "action" and reference.oracle.enemies:
                self.dead = True
            return result

    world = DeathEachFight()
    world.clock = exit_clock
    world.enemies = {10: 10}
    gate = CombatNavigationGate(
        make_live_env(world, max_faults=0),
        GateConfig(tmp_path / "combat_gate", wait_cap_seconds=5, max_deaths=5),
        budget_scale=5,
    )
    try:
        gate.reset()
        for death in range(1, 6):
            _, _, terminated, _, info = gate.step(np.array([1, 2]))
            assert terminated and info["outcome"] == "death"
            assert gate.stats.outcomes["death"] == death
            if death < 5:
                gate.reset()
        actions = world.action_count()
        handoffs = gate.stats.handoffs
        with pytest.raises(LiveBudgetExpired, match="Death limit reached"):
            gate.reset()
        assert world.action_count() == actions and gate.stats.handoffs == handoffs
        assert gate.stats.accepted == 5 and gate.stats.combat_steps == 5
        assert gate.state == "stopped" and not gate.cleanup_errors
    finally:
        gate.close()


@pytest.mark.parametrize("value", [0, 6, True, 1.5])
def test_navigation_scale_rejects_invalid_and_ungated_options(tmp_path, value):
    with pytest.raises(ValueError, match="Navigation budget scale"):
        CombatNavigationGate(make_live_env(World()), GateConfig(tmp_path), budget_scale=value)
    with pytest.raises(ValueError):
        LiveRunOptions(
            mode="random",
            out_dir=tmp_path,
            combat_gate=True,
            auto_navigate=True,
            navigation_budget_scale=value,
        )
    with pytest.raises(ValueError):
        LiveRunOptions(mode="random", out_dir=tmp_path, navigation_budget_scale=2)


@pytest.mark.parametrize("value", [0, 11, True, 1.5])
def test_death_limits_reject_invalid_or_ungated_options(tmp_path, value):
    with pytest.raises(ValueError, match="Death limit"):
        GateConfig(tmp_path, max_deaths=value)
    with pytest.raises(ValueError, match="Death limit"):
        LiveRunOptions(mode="random", out_dir=tmp_path, combat_gate=True, max_deaths=value)
    with pytest.raises(ValueError, match="Death limit"):
        LiveRunOptions(mode="random", out_dir=tmp_path, max_deaths=5)


def test_cli_passes_explicit_death_and_navigation_limits(tmp_path, monkeypatch):
    import sys

    from isaac_threrisaifuture import cli, live

    captured = []
    monkeypatch.setattr(live, "run_live", lambda options: captured.append(options) or tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "isaac-future",
            "live",
            "--mode",
            "random",
            "--confirmed-save-slot",
            "2",
            "--combat-gate",
            "--auto-navigate",
            "--navigation-budget-scale",
            "5",
            "--max-deaths",
            "5",
        ],
    )
    cli.main()
    assert captured[0].navigation_budget_scale == captured[0].max_deaths == 5


def outward_world(clock, resolution):
    world = World()
    world.clock, world.frame = clock, 10

    def snapshot():
        visit = 2 if resolution == "transition" and world.frame >= 18 else 1
        epoch = 2 if resolution == "foreign" and world.frame >= 17 else 1
        sample = navigable(snap(world.frame, visit=visit, epoch=epoch, clear=True))
        position = sample.player.position.model_copy(
            update={
                "x": 560.0 if world.frame == 10 else 590.0,
                "y": 200.0 if world.frame == 10 else 210.0,
            }
        )
        health = sample.player.health
        if resolution == "health" and world.frame >= 17:
            health = health.model_copy(update={"red_half_hearts": health.red_half_hearts - 1})
        sample = sample.model_copy(
            update={
                "player": sample.player.model_copy(update={"position": position, "health": health})
            }
        )
        nav = sample.oracle.navigation
        mask = list(nav.grid.walkable)
        mask[5 * nav.grid.width + 15] = "0"  # doorway boundary, not safe interior
        nav = nav.model_copy(
            update={"grid": nav.grid.model_copy(update={"walkable": "".join(mask)})}
        )
        return sample.model_copy(
            update={"oracle": sample.oracle.model_copy(update={"navigation": nav})}
        )

    world.snapshot = snapshot
    return world


@pytest.mark.parametrize("resolution", ["transition", "never", "health", "foreign"])
def test_accepted_release_waits_for_delayed_door_callback(tmp_path, exit_clock, resolution):
    world = outward_world(exit_clock, resolution)
    gate = gate_for(world, tmp_path)
    sample = world.snapshot()
    door = sample.oracle.navigation.doors[0]
    try:
        if resolution in ("health", "foreign"):
            with pytest.raises(NavigationStopped, match="waiting for door crossing"):
                gate._pulse(sample, door, exit_clock.now + 5)
            assert gate.nav_transitions == 0
        else:
            result = gate._pulse(sample, door, exit_clock.now + 5)
            assert result.room.visit_id == (2 if resolution == "transition" else 1)
            assert gate.nav_transitions == (1 if resolution == "transition" else 0)
            if resolution == "never":
                with pytest.raises(NavigationStopped, match="blocked"):
                    pulse_direction(result, door)  # no unsafe fallback after a missing callback
        assert [kind for kind, _ in world.commands] == ["action", "release"]
        assert gate.nav_commands == 2 and gate.nav_seconds <= 0.9
    finally:
        gate.close()


def test_door_callback_wait_cannot_extend_original_gate_deadline(tmp_path, exit_clock):
    from isaac_threrisaifuture.combat_gate import CombatGateExpired

    world = outward_world(exit_clock, "transition")
    gate = gate_for(world, tmp_path)
    sample = world.snapshot()
    started = exit_clock.now
    try:
        with pytest.raises(CombatGateExpired):
            gate._pulse(sample, sample.oracle.navigation.doors[0], started + 0.35)
        assert [kind for kind, _ in world.commands] == ["action", "release"]
        assert exit_clock.now - started <= 0.4
    finally:
        gate.close()
