"""OFFLINE schema 8 contract: doors, interactables, floor features, room classes, cap metrics."""

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml
from pydantic import ValidationError
from synthetic import door, enemy, event, frame, room_facts

from isaac_threrisaifuture.checkpoints import config_hash
from isaac_threrisaifuture.encoding import (
    CAPACITY,
    DOOR_FEATURES,
    ENEMY_IDENTITY_FEATURES,
    ENEMY_OFFSET,
    EXTRA_KINDS,
    EXTRA_OFFSET,
    IDENTITY_BUCKETS,
    MAP_CHANNELS,
    MAP_OFFSET,
    OBSERVATION_SIZE,
    ROOM_CLASSES,
    ROOM_OFFSET,
    ROOM_TYPES,
    SLOT_FEATURES,
    SLOT_WIDTH,
    encode,
    identity_bucket,
    room_class,
)
from isaac_threrisaifuture.entities import (
    ENTITY_CAPS,
    ENTITY_KINDS,
    FRAME_SCHEMA_VERSION,
    INTERACTABLE_CLASSES,
    OBSERVATION_SCHEMA_VERSION,
    OBSTACLE_CLASSES,
    DoorFacts,
    Entity,
    EntityFrame,
    MapRoom,
    Vec,
)
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import (
    CAP_FIELDS,
    FIELDS,
    EpisodeMetricsWriter,
    summary_row,
)
from isaac_threrisaifuture.episodes import Scenario, StepResult
from isaac_threrisaifuture.observation import ProtocolError, decode
from isaac_threrisaifuture.training import load_training_config

ROOT = Path(__file__).resolve().parents[1]


def wire(item: EntityFrame) -> dict[str, Any]:
    return json.loads(item.model_dump_json())


def decoded(payload: dict[str, Any]) -> EntityFrame:
    return decode(json.dumps(payload).encode(), EntityFrame, 131072)


def interactable(entity_id: int, x: float, cls: str | None = "beggar") -> Entity:
    return Entity(
        kind="interactable",
        entity_id=entity_id,
        spawn_generation=0,
        position=Vec(x=x, y=0),
        interactable_class=cls,  # type: ignore[arg-type]
    )


def block(vector: np.ndarray, kind: str) -> np.ndarray:
    offset = EXTRA_OFFSET
    for other in EXTRA_KINDS:
        if other == kind:
            return vector[offset : offset + CAPACITY[other] * SLOT_WIDTH[other]]
        offset += CAPACITY[other] * SLOT_WIDTH[other]
    raise AssertionError(kind)


# --- versions, caps, layout ----------------------------------------------------------------


def test_versions_caps_and_size():
    assert (OBSERVATION_SCHEMA_VERSION, FRAME_SCHEMA_VERSION) == (8, 6)
    assert EntityFrame.model_fields["observation_schema_version"].default == 6
    assert (
        CAPACITY
        == ENTITY_CAPS
        == {
            "enemy": 32,
            "projectile": 64,
            "obstacle": 64,
            "pickup": 24,
            "own_attack": 48,
            "bomb": 8,
            "interactable": 16,
        }
    )
    assert tuple(ENTITY_CAPS) == ENTITY_KINDS and sum(ENTITY_CAPS.values()) == 256
    assert OBSERVATION_SIZE == 9762
    assert len(ROOM_CLASSES) == 11 and DOOR_FEATURES == 4 + 11 and MAP_CHANNELS == 3 + 11
    assert SLOT_WIDTH["interactable"] == SLOT_FEATURES + len(INTERACTABLE_CLASSES) == 16


def test_schema_5_frames_are_refused():
    payload = wire(frame())
    payload["observation_schema_version"] = 5
    with pytest.raises(ProtocolError):
        decoded(payload)


def test_the_contract_hash_differs_from_schema_7_and_the_config_pins_8():
    config, digest = load_training_config(ROOT / "configs/training-pure-v4.yaml")
    raw = yaml.safe_load((ROOT / "configs/training-pure-v4.yaml").read_text("utf-8"))
    assert config.contract.observation_schema_version == 8 and config.contract.reward_version == 9
    assert config_hash(raw["contract"]) == digest
    raw["contract"]["observation_schema_version"] = 7
    assert config_hash(raw["contract"]) != digest


# --- room classes --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("room_type", "name"),
    [
        (1, "normal"), (5, "boss"), (4, "treasure"), (2, "shop"), (7, "secret"),
        (8, "secret"), (29, "secret"), (10, "curse"), (11, "challenge"), (17, "challenge"),
        (14, "devil_angel"), (15, "devil_angel"), (13, "sacrifice"), (9, "arcade"),
        (12, "special"), (24, "special"), (6, "special"), (3, "special"), (0, "special"),
        (31, "special"),
    ],
)  # fmt: skip
def test_room_type_groups(room_type, name):
    assert ROOM_CLASSES[room_class(room_type)] == name


# --- doors ---------------------------------------------------------------------------------


def door_block(vector: np.ndarray, slot: int) -> np.ndarray:
    at = ROOM_OFFSET + ROOM_TYPES + 3 + slot * DOOR_FEATURES
    return vector[at : at + DOOR_FEATURES]


def test_door_slots_encode_exists_open_locked_visited_and_the_class_one_hot():
    doors = [None] * 8
    doors[0] = door(open=True, target_type=1, visited=True)
    doors[3] = door(open=False, locked=True, target_type=4)
    doors[7] = door(open=False, target_type=None)  # target type unknown
    vector = encode(frame(room=room_facts(doors=doors))).vector
    assert door_block(vector, 0).tolist() == [1, 1, 0, 1] + [
        1.0 if name == "normal" else 0.0 for name in ROOM_CLASSES
    ]
    assert door_block(vector, 3).tolist() == [1, 0, 1, 0] + [
        1.0 if name == "treasure" else 0.0 for name in ROOM_CLASSES
    ]
    assert door_block(vector, 7).tolist() == [1, 0, 0, 0] + [0.0] * len(ROOM_CLASSES)
    for empty in (1, 2, 4, 5, 6):
        assert not door_block(vector, empty).any()


def test_door_wire_validation():
    ok = frame(room=room_facts(doors=[door(target_type=29), *[None] * 7]))
    assert decoded(wire(ok)) == ok
    for bad in (
        dict(open=1, locked=False, target_type=1, target_visited=False),
        dict(open=True, locked=None, target_type=1, target_visited=False),
        dict(open=True, locked=False, target_type=32, target_visited=False),
        dict(open=True, locked=False, target_type=-1, target_visited=False),
        dict(open=True, locked=False, target_type=1),
        dict(open=True, locked=False, target_type=1, target_visited=False, hidden=True),
    ):
        payload = wire(ok)
        payload["room"]["doors"][1] = bad
        with pytest.raises(ProtocolError):
            decoded(payload)
    with pytest.raises(ValidationError):
        DoorFacts(open=True, locked=False, target_type=1, target_visited="yes")  # type: ignore[arg-type]


# --- minimap classes -----------------------------------------------------------------------


def test_minimap_class_channels_follow_the_door_classes():
    rooms = [
        MapRoom(grid_index=i, shape=1, visited=True, current=False, room_type=t)
        for i, t in enumerate((1, 5, 4, 2, 7, 10, 11, 14, 13, 9, 24))
    ]
    vector = encode(frame(map=rooms)).vector
    classes = []
    for i in range(len(rooms)):
        base = MAP_OFFSET + i * MAP_CHANNELS
        assert vector[base : base + 3].tolist() == [1.0, 1.0, 0.0]
        hot = vector[base + 3 : base + MAP_CHANNELS]
        assert hot.sum() == 1.0
        classes.append(ROOM_CLASSES[int(hot.argmax())])
    assert classes == [
        "normal", "boss", "treasure", "shop", "secret", "curse", "challenge", "devil_angel",
        "sacrifice", "arcade", "special",
    ]  # fmt: skip


# --- grid classes and interactables --------------------------------------------------------


def test_new_obstacle_classes_exist_in_wire_order_before_wall_and_other():
    assert OBSTACLE_CLASSES[-2:] == ("wall", "other")
    for name in ("trapdoor", "crawlspace", "pressure_plate", "lock_block", "teleporter"):
        assert name in OBSTACLE_CLASSES
    item = Entity(
        kind="obstacle",
        entity_id=1,
        spawn_generation=0,
        position=Vec(x=5, y=0),
        obstacle_class="trapdoor",
    )
    assert decoded(wire(frame([item]))).entities[0].obstacle_class == "trapdoor"


def test_interactable_classes_encode_one_hot_after_the_base_features():
    items = [
        interactable(i + 1, 10.0 * (i + 1), name) for i, name in enumerate(INTERACTABLE_CLASSES)
    ]
    vector = block(encode(frame(items)).vector, "interactable")
    width = SLOT_WIDTH["interactable"]
    for slot, name in enumerate(INTERACTABLE_CLASSES):
        base = slot * width
        assert vector[base] == 1.0 and vector[base + 1] == pytest.approx(0.01 * (slot + 1))
        hot = vector[base + SLOT_FEATURES : base + width]
        assert hot.sum() == 1.0 and hot[INTERACTABLE_CLASSES.index(name)] == 1.0
    assert not vector[len(items) * width :].any()


def test_interactable_cap_is_16_nearest_first_with_overflow():
    items = [interactable(i, 10.0 * (20 - i)) for i in range(20)]
    encoded = encode(frame(items, source_overflow={"interactable": 2}))
    assert encoded.overflow == {"interactable": 6} and encoded.counts["interactable"] == 22
    vector = block(encoded.vector, "interactable")
    assert vector[1] == pytest.approx(0.01)  # nearest at x=10
    assert vector[SLOT_WIDTH["interactable"] * 15 + 1] == pytest.approx(0.16)  # 16th at x=160


def test_interactable_class_is_required_exactly_for_interactables():
    with pytest.raises(ValidationError):
        interactable(1, 5, None)
    with pytest.raises(ValidationError):
        interactable(1, 5, "pizza")
    with pytest.raises(ValidationError):
        Entity(
            kind="enemy",
            entity_id=1,
            spawn_generation=0,
            position=Vec(x=0, y=0),
            interactable_class="beggar",
        )
    ok = frame([interactable(1, 5, "heaven_door")])
    assert decoded(wire(ok)) == ok
    with pytest.raises(ValidationError):
        frame(source_overflow={"portal": 1})  # type: ignore[arg-type]


# --- cap metrics ---------------------------------------------------------------------------


class Crowd:
    """Backend whose frames hold a scripted enemy count (and observer overflow) per step."""

    supports_seed = False

    def __init__(self, counts, kinds=None):
        self.counts = list(counts)
        self.kinds = kinds  # (type, variant) per enemy index, or None for unknown identities
        self.frame_id = 1

    def _result(self, last: bool = False) -> StepResult:
        enemies, dropped = self.counts[self.frame_id - 1]
        items = [
            enemy(i, 10.0 + i, 0)
            if self.kinds is None
            else npc(i, 10.0 + i, *self.kinds[i % len(self.kinds)])
            for i in range(enemies)
        ]
        source = {"enemy": dropped} if dropped else {}
        events = (event("player_died", self.frame_id),) if last else ()
        return StepResult(
            frame(items, frame_id=self.frame_id, source_overflow=source), events, room_index=1
        )

    def start_episode(self, scenario, seed):
        self.frame_id = 1
        return self._result()

    def step(self, action, repeat):
        self.frame_id += 1
        return self._result(last=self.frame_id == len(self.counts))

    def release(self):
        pass

    def close(self):
        pass


def run_episode(env: IsaacCombatEnv, steps: int) -> dict[str, Any]:
    env.reset()
    info: dict[str, Any] = {}
    for _ in range(steps):
        info = env.step(np.array([0, 0, 0]))[4]
    return info["episode_summary"]


def test_cap_metrics_count_the_peak_and_the_share_of_overflow_steps(tmp_path: Path):
    # Four observations (reset and three steps): 5 enemies, 40 (cap 32), 32 plus 10 cut by the
    # observer, then 3 again. The terminal frame is counted before the summary is written.
    backend = Crowd([(5, 0), (40, 0), (32, 10), (3, 0)])
    scenario = Scenario("crowd", "train", 1, None, enemy_count=1, enemy_hp=1.0)
    env = IsaacCombatEnv(backend, [scenario])
    summary = run_episode(env, 3)
    assert summary["max_enemy"] == 42 and summary["max_bomb"] == 0
    assert summary["overflow_enemy"] == pytest.approx(2 / 4)
    assert summary["overflow_projectile"] == 0.0
    assert set(CAP_FIELDS) <= set(summary)
    assert set(CAP_FIELDS) == {
        *(f"max_{kind}" for kind in ENTITY_KINDS),
        *(f"overflow_{kind}" for kind in ENTITY_KINDS),
        "enemy_kinds",
    }
    assert set(CAP_FIELDS) <= set(FIELDS) and FIELDS[-1] == "wall_time"
    assert summary_row(summary)["max_enemy"] == 42
    path = tmp_path / "episodes.csv"
    EpisodeMetricsWriter(path).write(summary)
    row = next(csv.DictReader(path.open(encoding="utf-8")))
    assert row["max_enemy"] == "42" and float(row["overflow_enemy"]) == pytest.approx(0.5)
    # A new episode starts from zero.
    backend.counts = [(1, 0), (2, 0)]
    again = run_episode(env, 1)
    assert again["max_enemy"] == 2 and again["overflow_enemy"] == 0.0


# --- enemy identity ----------------------------------------------------------------------


def npc(entity_id: int, x: float, npc_type: int = 18, variant: int = 0, **changes: Any) -> Entity:
    facts: dict[str, Any] = dict(
        npc_type=npc_type,
        npc_variant=variant,
        npc_max_hp=10.0,
        boss=False,
        champion=False,
        flying=False,
        invulnerable=False,
    )
    return Entity(
        kind="enemy",
        entity_id=entity_id,
        spawn_generation=0,
        position=Vec(x=x, y=0),
        **(facts | changes),
    )


def test_enemy_slot_layout_and_size():
    assert IDENTITY_BUCKETS == 64 and ENEMY_IDENTITY_FEATURES == 6 + 64
    assert SLOT_WIDTH["enemy"] == SLOT_FEATURES + 70 == 78
    assert SLOT_WIDTH["projectile"] == SLOT_FEATURES  # the other blocks are unchanged
    assert OBSERVATION_SIZE == 7522 + 32 * 70


def test_identity_bucket_is_a_stable_integer_hash():
    # Known pairs pin the function: a change would silently renumber every learned kind.
    assert [
        identity_bucket(t, v) for t, v in [(0, 0), (18, 0), (18, 1), (26, 0), (1000, 4095)]
    ] == [
        0,
        26,
        1,
        9,
        3,
    ]
    assert all(
        0 <= identity_bucket(t, v) < 64 for t in range(0, 1001, 7) for v in range(0, 4096, 61)
    )
    assert len({identity_bucket(t, 0) for t in range(10, 100)}) > 40  # spreads well enough


def test_enemy_identity_features_follow_the_base_slot_features():
    vector = encode(frame([npc(1, 10, 18, 1, boss=True, flying=True, max_hp=None)])).vector
    base = ENEMY_OFFSET + SLOT_FEATURES
    assert vector[base : base + 5].tolist() == [1.0, 1.0, 0.0, 1.0, 0.0]  # valid, boss, ..., flying
    assert vector[base + 5] == pytest.approx(np.log1p(10.0) / np.log1p(10000.0))
    hot = vector[base + 6 : base + 6 + IDENTITY_BUCKETS]
    assert hot.sum() == 1.0 and hot[identity_bucket(18, 1)] == 1.0


def test_same_kind_gives_the_same_code_and_other_kinds_differ():
    one, two, other = (
        encode(frame([npc(i, 10.0, t, v)])).vector[ENEMY_OFFSET : ENEMY_OFFSET + 78]
        for i, (t, v) in enumerate([(18, 0), (18, 0), (18, 1)], 1)
    )
    assert np.array_equal(one, two) and not np.array_equal(one, other)


def test_unknown_identity_reads_zeros_with_the_valid_flag_clear():
    vector = encode(frame([enemy(1, 10.0, 0, hp=None)])).vector
    base = ENEMY_OFFSET
    assert vector[base] == 1.0  # present
    assert not vector[base + SLOT_FEATURES : base + 78].any()


def test_max_hp_feature_is_log_scaled_and_clipped():
    vector = encode(frame([npc(1, 10, npc_max_hp=1e6)])).vector
    assert vector[ENEMY_OFFSET + SLOT_FEATURES + 5] == 1.0


def test_enemy_identity_wire_validation():
    assert npc(1, 0).npc_type == 18
    for changes in (
        {"npc_type": 1001},
        {"npc_type": -1},
        {"npc_variant": 4096},
        {"npc_max_hp": -1.0},
        {"npc_max_hp": float("inf")},
        {"boss": None},  # the seven facts go together
    ):
        with pytest.raises(ValidationError):
            npc(1, 0, **changes)
    with pytest.raises(ValidationError):  # only enemies carry them
        Entity(
            kind="projectile",
            entity_id=1,
            spawn_generation=0,
            position=Vec(x=1, y=0),
            npc_type=18,
        )


def test_enemy_facts_round_trip_through_the_wire_and_old_frames_stay_valid():
    payload = wire(frame([npc(1, 10, 23, 2, boss=True)]))
    assert decoded(payload).entities[0].npc_variant == 2
    del payload["entities"][0]["npc_max_hp"]
    with pytest.raises(ProtocolError):
        decoded(payload)  # partial facts are refused
    plain = wire(frame([enemy(1, 10, 0)]))
    assert decoded(plain).entities[0].npc_type is None


def test_enemy_kinds_metric_counts_distinct_type_variant_pairs():
    pairs = [(18, 0), (18, 0), (23, 1)]
    seen = encode(frame([npc(i, 10.0 + i, t, v) for i, (t, v) in enumerate(pairs, 1)]))
    assert seen.enemy_kinds == {(18, 0), (23, 1)}
    assert "enemy_kinds" in CAP_FIELDS and "enemy_kinds" in FIELDS
    scenario = Scenario("crowd", "train", 1, None, enemy_count=1, enemy_hp=1.0)
    backend = Crowd([(1, 0), (2, 0), (3, 0), (3, 0)], kinds=[(18, 0), (23, 1), (18, 0)])
    assert run_episode(IsaacCombatEnv(backend, [scenario]), 3)["enemy_kinds"] == 2
    unknown = Crowd([(2, 0), (2, 0)])
    assert run_episode(IsaacCombatEnv(unknown, [scenario]), 1)["enemy_kinds"] == 0
