"""Offline exposed-start curriculum tests. Synthetic physics is not native evidence."""

import json
import shutil
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import gymnasium as gym
import numpy as np
import pytest
from test_firing_position import sample

from isaac_threrisaifuture import exposed_start as es
from isaac_threrisaifuture.checkpoints import CheckpointError
from isaac_threrisaifuture.live import LiveRunOptions, LiveSnapshot
from isaac_threrisaifuture.observer_client import ObserverConfig

SPEC = es.SetupSpec()


class Scene:
    """Room-83 client: one-frame damped physics per action command, one snapshot per take."""

    def __init__(self, *, pos=(560.0, 280.0), vel=(0.0, 0.0), hold=None):
        self.hold = hold  # forced native frames per command (old three-frame repeat)
        self.pos, self.vel = np.array(pos), np.array(vel)
        self.frame, self.health, self.visit, self.room = 10, 6, 1, 83
        self.target = np.array(SPEC.target)
        self.weapon, self.velocity_known, self.clear, self.dead = "plain_tears", True, False, False
        self.walkable = "1" * 144
        self.commands: list[tuple[str, str | None, str | None, int | None]] = []
        self.hooks: dict[int, object] = {}
        self.connected, self.config = True, ObserverConfig()

    def snapshot(self) -> LiveSnapshot:
        raw = sample(self.frame, visit=self.visit, room=self.room).model_dump(mode="json")
        pos = {"x": float(self.pos[0]), "y": float(self.pos[1])}
        raw["player"]["position"] = pos
        raw["entity_frame"]["player_position"] = pos
        raw["entity_frame"]["player_velocity"] = (
            {"x": float(self.vel[0]), "y": float(self.vel[1])} if self.velocity_known else None
        )
        raw["entity_frame"]["health"]["red_half_hearts"] = self.health
        raw["entity_frame"]["health"]["soul_half_hearts"] = 0
        raw["player"]["health"] = raw["entity_frame"]["health"]
        rel = self.target - self.pos
        raw["entity_frame"]["entities"][0]["position"] = {"x": rel[0], "y": rel[1]}
        raw["oracle"]["room_clear"], raw["oracle"]["player_dead"] = self.clear, self.dead
        raw["oracle"]["navigation"]["grid"].update(width=16, height=9, walkable=self.walkable)
        raw["oracle"]["firing"] = None
        raw["combat_geometry"] = {
            "version": 2,
            "frame_id": self.frame,
            "weapon": self.weapon,
            "tear_range": 260.0 if self.weapon == "plain_tears" else None,
            "movement": [True, True, True, True],
            "enemies": [{"entity_id": 1, "clear": True}] if self.weapon == "plain_tears" else [],
        }
        return LiveSnapshot.model_validate(raw)

    def take(self, timeout):
        self.frame += 1
        return self.snapshot()

    def drain(self):
        return []

    def command(self, kind, reference, move=None, shoot=None, frames=None):
        self.commands.append((kind, move, shoot, frames))
        if kind == "action":
            u = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}.get(move, (0, 0))
            for _ in range(self.hold or frames or 1):
                self.vel = 0.8 * self.vel + 0.6 * np.array(u)
                self.pos = self.pos + self.vel
            hook = self.hooks.pop(self.actions(), None)
            if hook is not None:
                hook(self)
        return SimpleNamespace(status="accepted", frame_id=self.frame)

    def actions(self):
        return sum(kind == "action" for kind, *_ in self.commands)


def setup(scene, **kwargs):
    return es.run_setup(scene, SPEC, deadline=1e18, **kwargs)


def test_caps_manifest_is_bounded_and_hashed():
    record = es.PILOT_CAPS.as_record()
    assert record["experiment"] == es.EXPERIMENT and len(record["sha256"]) == 64
    assert es.PILOT_CAPS.cumulative_target == 26368 + es.PILOT_CAPS.learning_steps
    with pytest.raises(ValueError, match="lease"):
        es.PilotCaps(learning_seconds=250)
    with pytest.raises(ValueError, match="command"):
        es.PilotCaps(learning_steps=2900)
    with pytest.raises(ValueError, match="zero"):
        es.PilotCaps(retries=1)


@pytest.mark.parametrize("seed", range(16))
def test_one_frame_route_settles_at_both_waypoints(seed):
    rng = np.random.default_rng(seed)
    scene = Scene(pos=np.array(SPEC.door) + rng.uniform(-10, 10, 2), vel=rng.uniform(-3, 3, 2))
    result = setup(scene)
    assert result.commands <= SPEC.max_commands and result.direction == 1  # left
    assert abs(scene.pos[0] - 320) <= 6 and abs(scene.pos[1] - 200) <= 4
    actions = [c for c in scene.commands if c[0] == "action"]
    assert all(shoot == "none" and frames == 1 for _, _, shoot, frames in actions)
    assert scene.commands[-1][0] == "release"


def test_old_three_frame_repeat_does_not_converge():
    with pytest.raises(es.SetupRefused, match="command cap"):
        setup(Scene(hold=3))


def test_route_step_brakes_before_advancing():
    state = es.RouteState()
    assert es.route_step(state, (560, 201), (2.0, 0.0), SPEC) == "none" and state.braking
    assert es.route_step(state, (560, 201), (0.0, 0.0), SPEC) == "none"
    assert state.waypoint == 1 and not state.braking
    assert es.route_step(state, (560, 200), (0.0, 0.0), SPEC) == "left"


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (lambda s: setattr(s, "visit", 2), "changed"),
        (lambda s: setattr(s, "weapon", "unsupported"), "Weapon"),
        (lambda s: setattr(s, "health", 5), "health loss"),
        (lambda s: setattr(s, "target", s.target + 30), "target"),
        (lambda s: setattr(s, "walkable", "0" + "1" * 143), "grid"),
        (lambda s: setattr(s, "velocity_known", False), "velocity"),
        (lambda s: setattr(s, "clear", True), "terminal"),
    ],
)
def test_setup_refuses_changes_and_releases(change, match):
    scene = Scene()
    scene.hooks[5] = change
    with pytest.raises(es.SetupRefused, match=match):
        setup(scene)
    assert scene.commands[-1][0] == "release" and scene.actions() == 5


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (lambda s: setattr(s, "room", 84), "room"),
        (lambda s: setattr(s, "pos", np.array([400.0, 280.0])), "door"),
        (lambda s: setattr(s, "weapon", "unsupported"), "weapon"),
        (lambda s: setattr(s, "walkable", "0" * 144), "grid"),
    ],
)
def test_precheck_refuses_without_commands(change, match):
    scene = Scene()
    change(scene)
    with pytest.raises(es.SetupRefused, match=match):
        setup(scene)
    assert scene.commands == []


def test_setup_command_cap_and_deadline_refuse():
    scene = Scene()
    with pytest.raises(es.SetupRefused, match="command cap"):
        es.run_setup(scene, replace(SPEC, max_commands=3), deadline=1e18)
    assert scene.actions() == 3 and scene.commands[-1][0] == "release"
    with pytest.raises(es.SetupRefused, match="deadline"):
        es.run_setup(Scene(), SPEC, deadline=0.0)


def test_unaligned_handoff_is_refused():
    scene = Scene()
    scene.target = np.array([80.0, 100.0])  # never on the final waypoint's axes
    spec = replace(SPEC, target=(80.0, 100.0))
    with pytest.raises(es.SetupRefused, match="clear aligned"):
        es.run_setup(scene, spec, deadline=1e18)


class Learner(gym.Env):
    """Passthrough env exposing the backend surface ExposedStartEnv reads."""

    observation_space = gym.spaces.Box(-1, 1, (2,))
    action_space = gym.spaces.Discrete(2)

    def __init__(self, scene):
        self.scene, self.released = scene, 0
        self.controller = SimpleNamespace(backend=self)
        self.latest = None

    def release(self):
        self.released += 1

    def reset(self, **kwargs):
        self.scene.frame += 1
        self.latest = self.scene.snapshot()
        return np.zeros(2, np.float32), {}

    def step(self, action):
        self.scene.frame += 1
        self.latest = self.scene.snapshot()
        return np.ones(2, np.float32), 0.5, False, False, {"k": 1}


def handed_off():
    scene = Scene()
    result = setup(scene)
    return scene, result


def test_learner_boundary_passes_through_and_checks_fresh_handoff():
    scene, result = handed_off()
    env = es.ExposedStartEnv(Learner(scene), result, SPEC)
    observation, info = env.reset()
    assert info == {} and not observation.any()
    assert env.step(0)[1:] == (0.5, False, False, {"k": 1})
    assert [s.frame for s in env.samples][0] > result.handoff_frame


@pytest.mark.parametrize(
    "change", [lambda s: setattr(s, "visit", 9), lambda s: setattr(s, "target", s.target + 30)]
)
def test_stale_handoff_refused_before_learning(change):
    scene, result = handed_off()
    change(scene)
    learner = Learner(scene)
    with pytest.raises(es.SetupRefused, match="Stale"):
        es.ExposedStartEnv(learner, result, SPEC).reset()
    assert learner.released == 1


def test_handoff_frame_must_advance():
    scene, result = handed_off()
    env = es.ExposedStartEnv(Learner(scene), replace(result, handoff_frame=10**9), SPEC)
    with pytest.raises(es.SetupRefused, match="newer"):
        env.reset()


@pytest.mark.parametrize(("health", "match"), [(1, "minimum"), (2, "cumulative")])
def test_training_health_stops_before_next_action(health, match):
    scene, result = handed_off()
    learner = Learner(scene)
    env = es.ExposedStartEnv(learner, result, SPEC)
    env.reset()
    scene.health = health
    env.step(0)
    with pytest.raises(es.CurriculumStop, match=match):
        env.step(0)
    assert learner.released == 1


def test_healed_damage_still_counts_toward_loss():
    scene, result = handed_off()
    env = es.ExposedStartEnv(Learner(scene), result, SPEC)
    env.reset()
    for health in (4, 6, 4):
        scene.health = health
        env.step(0)
    assert env.health_loss == 4 and env.stop_reason is not None


def test_options_require_exact_opt_in(tmp_path):
    base = dict(mode="train", out_dir=tmp_path)
    ok = dict(
        base, resume=True, combat_gate=True, auto_navigate=True,
        navigation_time_dominant=True, combat_geometry=True, boundary_progress_reward=True,
        firing_position_reward=True, max_deaths=1, max_faults=0, session_deadline=1.0,
        exposed_start=True, exposed_start_parent=tmp_path, combat_trace_bytes=1024,
    )  # fmt: skip
    assert not LiveRunOptions(**base).exposed_start
    LiveRunOptions(**ok)
    with pytest.raises(ValueError):
        LiveRunOptions(**base, exposed_start_parent=tmp_path)
    for name, value in [("max_deaths", 2), ("resume", False), ("session_deadline", None),
                        ("exposed_start_parent", None), ("combat_trace_bytes", 0)]:  # fmt: skip
        with pytest.raises(ValueError):
            LiveRunOptions(**{**ok, name: value})


def samples(points, *, hp=10.0, health=6, step=30):
    return [
        es.PhaseSample(i * step, x, y, health, ((1, hp),), False, False, True, ("s", 1, 1))
        for i, (x, y) in enumerate(points)
    ]


def test_phase_metrics_and_stagnation_windows():
    still = samples([(70.0, 410.0)] * 12)
    metrics = es.phase_metrics("frozen_parent", still)
    assert metrics["stagnation_windows_10s"] == 1 and metrics["near_old_corner"] == 12
    assert metrics["decisions"] == 11 and metrics["coverage"] == "partial"
    moving = samples([(70.0 + 25 * i, 410.0) for i in range(12)])
    assert es.phase_metrics("x", moving)["stagnation_windows_10s"] == 0
    hit = still[:6] + [replace(s, enemy_hp=((1, 5.0),)) for s in still[6:]]
    hits = es.phase_metrics("x", hit)
    assert hits["enemy_hp_loss_lower_bound"] == 5.0 and hits["stagnation_windows_10s"] == 0
    assert es.phase_metrics("x", [], status="not_run")["start"] is None


def test_report_is_labelled_observational(tmp_path):
    report = es.write_report(tmp_path / "r.json", [], es.PILOT_CAPS)
    saved = json.loads((tmp_path / "r.json").read_text())
    assert saved == report and saved["comparison"] == "observational"


def test_frozen_phase_not_run_is_never_substituted(tmp_path):
    options = SimpleNamespace(stop_file=None)
    kwargs = dict(cfg_hash="x", seed=20, deadline=1e18, record=lambda *_: None, sink=None,
                  spec=SPEC)  # fmt: skip
    missing = es.run_frozen_phase("frozen_child", None, None, options, **kwargs)
    assert missing["status"] == "not_run" and missing["samples"] == 0
    capped = es.run_frozen_phase(
        "frozen_parent", None, tmp_path, options, unavailable="Output cap exceeded", **kwargs
    )
    assert capped["status"] == "not_run" and capped["reason"] == "Output cap exceeded"


def test_phase_client_does_not_close_shared_client():
    scene = Scene()
    scene.closed = False
    scene.close = lambda: setattr(scene, "closed", True)
    proxy = es.PhaseClient(scene)
    proxy.close()
    assert not scene.closed and proxy.frame == scene.frame


# --- branch -----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    from test_checkpoint_policy import CFG_HASH, RAW_CONFIG, SEED, synthetic_env

    from isaac_threrisaifuture.training import TrainingConfig, train

    run = tmp_path_factory.mktemp("parent-run")
    result = train(TrainingConfig.model_validate(RAW_CONFIG), CFG_HASH, seed=SEED,
                   env_factory=synthetic_env, out_dir=run)  # fmt: skip
    return run / "checkpoints" / result.checkpoint_id, CFG_HASH, SEED


def make_parent(tmp_path: Path, trained):
    source, cfg_hash, seed = trained
    run = tmp_path / "parent-run" / "checkpoints"
    run.mkdir(parents=True)
    shutil.copytree(source, run / source.name)
    (run / "latest.txt").write_text(source.name)
    return run / source.name, cfg_hash, run / "latest.txt", seed


def test_branch_copies_exactly_and_leaves_parent_unchanged(tmp_path, trained):
    parent, cfg_hash, pointer, seed = make_parent(tmp_path, trained)
    before = (es._hashes(parent), pointer.read_bytes())
    child_root = tmp_path / "child"
    args = dict(seed=seed, cfg_hash=cfg_hash, reward_contract="combat-v1", observation_schema=1)
    receipt = es.branch_checkpoint(parent, child_root, **args)
    child = child_root / f"seed-{seed}" / "checkpoints" / parent.name
    assert receipt["artifact_sha256"] == before[0] == es._hashes(child)
    assert (child_root / f"seed-{seed}" / "checkpoints" / "latest.txt").read_text() == parent.name
    assert json.loads((child_root / f"seed-{seed}" / "branch-receipt.json").read_text()) == receipt
    assert (es._hashes(parent), pointer.read_bytes()) == before
    with pytest.raises(CheckpointError, match="already exists"):
        es.branch_checkpoint(parent, child_root, **args)
    with pytest.raises(CheckpointError):
        es.branch_checkpoint(parent, tmp_path / "other", **{**args, "seed": seed + 1})
    with pytest.raises(CheckpointError, match="one existing"):
        es.branch_checkpoint(parent.parent, tmp_path / "third", **args)


def test_interrupted_branch_publishes_no_pointer(tmp_path, trained):
    parent, cfg_hash, _, seed = make_parent(tmp_path, trained)

    def broken(source, target):
        target.mkdir()
        (target / "partial").write_text("x")
        raise OSError("disk full")

    with pytest.raises(OSError):
        es.branch_checkpoint(
            parent, tmp_path / "child", seed=seed, cfg_hash=cfg_hash, reward_contract="combat-v1",
            observation_schema=1, copy=broken,
        )  # fmt: skip
    assert not (tmp_path / "child" / f"seed-{seed}" / "checkpoints").exists()


def pilot_options(tmp_path, trained, **changes):
    import yaml
    from test_checkpoint_policy import RAW_CONFIG

    from isaac_threrisaifuture.checkpoints import read_manifest

    parent, cfg_hash, _, seed = make_parent(tmp_path, trained)
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(RAW_CONFIG))
    out = tmp_path / "child"
    es.branch_checkpoint(parent, out, seed=seed, cfg_hash=cfg_hash,
                         reward_contract="combat-v1", observation_schema=1)  # fmt: skip
    caps = es.PilotCaps(cumulative_target=read_manifest(parent).timesteps + 2048)
    options = LiveRunOptions(
        mode="train", out_dir=out, config_path=config, seed=seed, resume=True,
        combat_gate=True, auto_navigate=True, navigation_time_dominant=True,
        combat_geometry=True, boundary_progress_reward=True, firing_position_reward=True,
        max_deaths=1, max_faults=0, session_deadline=1e18, exposed_start=True,
        exposed_start_parent=parent, combat_trace_bytes=1024,
        steps=caps.cumulative_target, combat_progress_updates=caps.progress_updates,
    )  # fmt: skip
    return replace(options, **changes), caps


def test_refused_setup_reports_without_learning(tmp_path, trained):
    options, caps = pilot_options(tmp_path, trained)
    scene = Scene()
    scene.room = 84
    records = []
    report = es.run_pilot(scene, options, lambda *a: records.append(a), lambda _: None,
                          tmp_path, caps=caps)  # fmt: skip
    assert [(p["phase"], p["status"]) for p in report["phases"]] == [
        ("setup", "refused"), ("learning", "not_run"),
        ("frozen_parent", "not_run"), ("frozen_child", "not_run")]  # fmt: skip
    assert scene.commands == [] and (tmp_path / "exposed-start-phases.json").exists()
    assert report["phases"][0]["start"]["room_index"] == 84
    initial = [data for name, data in records if name == "exposed_start_setup_observation"]
    assert len(initial) == 1 and initial[0]["entity_frame"] is not None


def test_pilot_refuses_options_outside_cap_manifest(tmp_path, trained):
    options, caps = pilot_options(tmp_path, trained, steps=10**6)
    with pytest.raises(ValueError, match="cap manifest"):
        es.run_pilot(Scene(), options, lambda *a: None, lambda _: None, tmp_path, caps=caps)


def test_expired_setup_rejects_even_a_queued_snapshot():
    scene = Scene()
    scene.drain = lambda: [scene.snapshot()]
    with pytest.raises(es.SetupRefused, match="deadline"):
        es.run_setup(scene, SPEC, deadline=0)
    assert scene.commands == []


def test_metrics_use_native_30hz_and_count_nonoverlapping_windows():
    still = samples([(320.0, 200.0)] * 22)
    metrics = es.phase_metrics("learning", still)
    assert metrics["active_seconds"] == 21
    assert metrics["stagnation_windows_10s"] == 2
    shifted = still[:10] + [
        replace(s, context=("next", 1, 2), frame=s.frame - 300) for s in still[10:]
    ]
    assert es.phase_metrics("learning", shifted)["active_seconds"] == 20


def test_unknown_weapon_is_not_a_known_absent_shot():
    scene = Scene()
    scene.weapon = "unsupported"
    assert es.sample_of(scene.snapshot()).clear_shot is None


def test_observed_death_blocks_reset_even_with_nonzero_health(monkeypatch):
    scene, result = handed_off()
    learner = Learner(scene)
    env = es.ExposedStartEnv(learner, result, SPEC)
    env.reset()
    scene.dead = True
    env.step(0)
    monkeypatch.setattr(learner, "reset", lambda **_: pytest.fail("reset after death"))
    with pytest.raises(es.CurriculumStop, match="death"):
        env.reset()


def test_live_reader_disconnects_on_death_without_waiting_for_optimizer(monkeypatch):
    from unittest.mock import Mock

    from isaac_threrisaifuture.live import LiveClient

    scene = Scene()
    scene.dead = True
    client = LiveClient(ObserverConfig(), stop_on_death=True)
    peer = Mock()
    monkeypatch.setattr(client, "_peer", peer)
    monkeypatch.setattr(
        client, "_read_line", lambda _: scene.snapshot().model_dump_json().encode("utf-8")
    )
    monkeypatch.setattr(client, "_validate_snapshot", lambda _: None)
    client._read_loop()
    assert not client.connected and client.fatal_snapshot.oracle.player_dead
    assert client.take(0.01).oracle.player_dead
    peer.shutdown.assert_called_once()


def test_shared_command_cap_and_release_after_exhaustion(tmp_path):
    scene = Scene()
    caps = replace(
        es.PILOT_CAPS,
        action_commands=6,
        setup_commands=1,
        learning_steps=1,
        frozen_decisions=1,
        frozen_setup_commands=1,
    )
    client = es.PilotClient(scene, 1e18, tmp_path, caps)
    for _ in range(6):
        client.command("action", scene.snapshot(), move="none", shoot="none", frames=1)
    with pytest.raises(es.CurriculumStop, match="command"):
        client.command("action", scene.snapshot(), frames=1)
    client.command("release", scene.snapshot())
    assert scene.actions() == 6 and scene.commands[-1][0] == "release"


@pytest.mark.parametrize(
    ("name", "where", "match"),
    [
        ("output_bytes", "data.txt", "output"),
        ("trace_bytes", "diagnostics/policy.jsonl", "trace"),
    ],
)
def test_shared_file_caps_checked_before_actions(tmp_path, name, where, match):
    path = tmp_path / where
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("overflow")
    scene = Scene()
    client = es.PilotClient(scene, 1e18, tmp_path, replace(es.PILOT_CAPS, **{name: 1}))
    with pytest.raises(es.CurriculumStop, match=match):
        client.command("action", scene.snapshot(), frames=1)
    assert scene.commands == []


def test_last_command_boundary_rechecks_handoff(tmp_path):
    scene, result = handed_off()
    learner = Learner(scene)
    env = es.ExposedStartEnv(learner, result, SPEC)
    env.reset()
    client = es.PilotClient(scene, 1e18, tmp_path, es.PILOT_CAPS)

    def check(snap):
        reason = env._stale(snap)
        if reason:
            raise es.SetupRefused(reason)

    client._pilot_first = check
    scene.target += 30
    before = scene.actions()
    with pytest.raises(es.SetupRefused):
        client.command("action", scene.snapshot(), move="left", frames=3)
    assert scene.actions() == before


def test_lost_frozen_transport_never_reconnects_unverified_instance(tmp_path):
    scene = Scene()
    scene.connected = False
    scene.connect = lambda: pytest.fail("unverified reconnect")
    result = es.run_frozen_phase(
        "frozen_parent",
        scene,
        tmp_path,
        SimpleNamespace(stop_file=None),
        cfg_hash="x",
        seed=20,
        deadline=1e18,
        record=lambda *_: None,
        sink=None,
        spec=SPEC,
    )
    assert result["status"] == "not_run" and "Transport" in result["reason"]


def test_shared_deadline_cannot_be_renewed_by_phase(tmp_path, monkeypatch):
    scene = Scene()
    monkeypatch.setattr(es.time, "monotonic", lambda: 100.0)
    client = es.PilotClient(scene, 105.0, tmp_path, es.PILOT_CAPS)
    client.phase("learning", 180.0)
    assert client._pilot_deadline == 105.0
    monkeypatch.setattr(es.time, "monotonic", lambda: 105.0)
    with pytest.raises(es.CurriculumStop, match="deadline"):
        client.command("action", scene.snapshot(), frames=1)
    client.command("release", scene.snapshot())
    assert scene.actions() == 0


def test_default_reader_does_not_enable_curriculum_death_latch(monkeypatch):
    from unittest.mock import Mock

    from isaac_threrisaifuture.live import LiveClient

    scene = Scene()
    scene.dead = True
    client = LiveClient(ObserverConfig())
    peer = Mock()
    monkeypatch.setattr(client, "_peer", peer)
    reads = iter([scene.snapshot().model_dump_json().encode("utf-8")])
    monkeypatch.setattr(client, "_read_line", lambda _: next(reads))
    monkeypatch.setattr(client, "_validate_snapshot", lambda _: None)
    client._read_loop()
    assert client.fatal_snapshot is None
    peer.shutdown.assert_not_called()


class EnteringScene(Scene):
    """Visible set becomes available later than the initial oracle membership."""

    def __init__(self, visible_at=4, change=None, clock=None):
        super().__init__()
        self.readings, self.visible_at, self.change, self.clock = 0, visible_at, change, clock
        self.first_action_at = None

    def take(self, timeout):
        self.readings += 1
        if self.clock is not None:
            self.clock[0] += 0.1
        if self.readings == 2 and self.change is not None:
            self.change(self)
        return super().take(timeout)

    def snapshot(self):
        snap = super().snapshot()
        if self.readings < self.visible_at:
            raw = snap.model_dump(mode="json")
            raw["entity_frame"]["entities"] = []
            raw["combat_geometry"]["enemies"] = []
            snap = LiveSnapshot.model_validate(raw)
        return snap

    def command(self, kind, reference, **kwargs):
        if kind == "action" and self.first_action_at is None:
            self.first_action_at = self.readings
        return super().command(kind, reference, **kwargs)


def test_entry_waits_without_commands_until_existing_target_is_visible():
    scene, records = EnteringScene(visible_at=61), []
    result = es.run_setup(scene, SPEC, deadline=1e18, record=lambda *a: records.append(a))
    assert result.commands == scene.actions() and scene.first_action_at == 61
    states = [data for name, data in records if name == "exposed_start_readiness"]
    assert [s["status"] for s in states] == ["waiting", "ready"]
    assert states[-1]["snapshots"] == 61


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (lambda s: setattr(s, "visit", 2), "Context changed"),
        (lambda s: setattr(s, "health", 5), "health loss"),
        (lambda s: setattr(s, "walkable", "0" * 144), "grid changed"),
        (lambda s: setattr(s, "weapon", "unsupported"), "weapon"),
        (lambda s: setattr(s, "dead", True), "combat"),
        (lambda s: setattr(s, "pos", np.array([400.0, 280.0])), "door"),
    ],
)
def test_entry_wait_refuses_changed_state_before_any_action(change, match):
    scene = EnteringScene(change=change)
    with pytest.raises(es.SetupRefused, match=match):
        setup(scene)
    assert scene.commands == []


def test_entry_wait_refuses_changed_enemy_membership():
    scene = EnteringScene()
    original = scene.snapshot

    def snapshot():
        raw = original().model_dump(mode="json")
        if scene.readings >= 2:
            raw["oracle"]["enemies"][0]["entity_id"] += 1
        return LiveSnapshot.model_validate(raw)

    scene.snapshot = snapshot
    with pytest.raises(es.SetupRefused, match="membership changed"):
        setup(scene)
    assert scene.commands == []


def test_entry_wait_has_its_own_snapshot_cap():
    scene = EnteringScene(visible_at=1000)
    with pytest.raises(es.SetupRefused, match="snapshot cap"):
        es.run_setup(scene, replace(SPEC, entry_snapshots=3), deadline=1e18)
    assert scene.readings == 3 and scene.commands == []


@pytest.mark.parametrize("outer", [False, True])
def test_entry_wait_cannot_renew_its_own_or_outer_deadline(monkeypatch, outer):
    clock = [0.0]
    monkeypatch.setattr(es.time, "monotonic", lambda: clock[0])
    scene = EnteringScene(visible_at=1000, clock=clock)
    with pytest.raises(es.SetupRefused, match="visibility deadline"):
        es.run_setup(scene, replace(SPEC, entry_seconds=0.25), deadline=0.25 if outer else 1e18)
    assert scene.readings <= 4 and scene.commands == []


def test_visible_wrong_target_is_refused_immediately_without_waiting():
    scene = EnteringScene(visible_at=1)
    scene.target += 30
    with pytest.raises(es.SetupRefused, match="target unavailable or moved"):
        setup(scene)
    assert scene.readings == 1 and scene.commands == []


def test_entry_wait_honors_user_stop_without_movement(tmp_path):
    stop = tmp_path / "stop.request"
    scene = EnteringScene(change=lambda _: stop.touch())
    with pytest.raises(es.SetupRefused, match="cancellation"):
        es.run_setup(scene, SPEC, deadline=1e18, stop_file=stop)
    assert scene.commands == []


def test_wrong_target_after_visibility_wait_is_not_substituted():
    scene = EnteringScene(change=lambda s: setattr(s, "target", s.target + 30))
    with pytest.raises(es.SetupRefused, match="target unavailable or moved"):
        setup(scene)
    assert scene.readings == 4 and scene.commands == []
