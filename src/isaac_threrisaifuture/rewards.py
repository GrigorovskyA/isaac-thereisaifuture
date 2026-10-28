"""Event-driven reward ledgers: combat reward-v1 and outcome-only reward-v4 to v9.

Coefficients are hypotheses, not tuned values.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

import yaml

from .encoding import room_diagonal
from .entities import BOSS_ROOM_TYPE, EntityFrame, OracleDoor, OracleEvent
from .env import UPDATES_PER_SECOND
from .stall_watchdog import DEFAULT_STALL_SECONDS

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "configs" / "reward-v1.yaml"
_KEYS = (
    "enemy_hp_fraction_total",
    "enemy_kill",
    "room_clear_first",
    "enemy_damage_half_heart",
    "death",
    "active_combat_second",
)


@dataclass(frozen=True)
class CombatCoefficients:
    enemy_hp_fraction_total: float
    enemy_kill: float
    room_clear_first: float
    enemy_damage_half_heart: float
    death: float
    active_combat_second: float

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG) -> Self:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("reward_version") != 1:
            raise ValueError("Unsupported reward configuration version")
        if "combat" not in raw.get("enabled", []):
            raise ValueError("The combat reward group is not enabled")
        combat = raw.get("combat")
        if not isinstance(combat, dict) or set(combat) != set(_KEYS):
            raise ValueError(f"The combat section must define exactly {_KEYS}")
        return cls(**{key: float(combat[key]) for key in _KEYS})


@dataclass
class RewardLedger:
    """Each reward source pays at most once; healed enemy HP cannot be farmed again."""

    coefficients: CombatCoefficients
    ignored_events: int = 0
    _seen: set[tuple[object, ...]] = field(default_factory=set)
    _initial_hp: dict[tuple[int, int], float] = field(default_factory=dict)
    _removed: dict[tuple[int, int], float] = field(default_factory=dict)
    _killed: set[tuple[int, int]] = field(default_factory=set)
    _alive: set[tuple[int, int]] = field(default_factory=set)
    _cleared: bool = False
    _dead: bool = False

    def reset(self, episode_id: int) -> None:
        self._seen.clear()
        self._initial_hp.clear()
        self._removed.clear()
        self._killed.clear()
        self._alive.clear()
        self._cleared = self._dead = False

    def consume(
        self, events: Sequence[OracleEvent], elapsed_updates: int
    ) -> tuple[float, dict[str, float]]:
        c = self.coefficients
        parts = {"enemy_damage": 0.0, "enemy_kill": 0.0, "room_clear": 0.0}
        parts.update(damage_taken=0.0, death=0.0, time=0.0)
        if self._alive and not self._dead:
            parts["time"] = c.active_combat_second * elapsed_updates / UPDATES_PER_SECOND
        for event in events:
            # ponytail: identical simultaneous events collapse; upgrade needs an event sequence ID.
            identity = (
                event.kind,
                event.frame_id,
                event.entity_id,
                event.spawn_generation,
                event.amount,
                event.damage_source,
            )
            if identity in self._seen:
                self.ignored_events += 1
                continue
            self._seen.add(identity)
            self._apply(event, parts)
        return sum(parts.values()), parts

    def _apply(self, event: OracleEvent, parts: dict[str, float]) -> None:
        c = self.coefficients
        enemy: tuple[int, int] | None = None
        if event.entity_id is not None and event.spawn_generation is not None:
            enemy = (event.entity_id, event.spawn_generation)
        if event.kind == "enemy_spawned" and enemy and event.amount and event.amount > 0:
            if enemy not in self._initial_hp:
                self._initial_hp[enemy] = event.amount
                self._alive.add(enemy)
        elif event.kind == "enemy_damaged" and enemy and event.amount is not None:
            initial = self._initial_hp.get(enemy)
            if initial is None:
                self.ignored_events += 1  # unknown enemy: no reward without an initial HP
                return
            credited = min(event.amount, initial - self._removed.get(enemy, 0.0))
            if credited > 0:
                self._removed[enemy] = self._removed.get(enemy, 0.0) + credited
                parts["enemy_damage"] += c.enemy_hp_fraction_total * credited / initial
        elif event.kind == "enemy_killed" and enemy:
            self._alive.discard(enemy)
            if enemy in self._initial_hp and enemy not in self._killed:
                self._killed.add(enemy)
                parts["enemy_kill"] += c.enemy_kill
        elif event.kind == "room_cleared" and not self._cleared:
            self._cleared = True
            parts["room_clear"] += c.room_clear_first
        elif event.kind == "player_damaged" and event.damage_source == "enemy":
            parts["damage_taken"] += c.enemy_damage_half_heart * (event.amount or 0.0)
        elif event.kind == "player_died" and not self._dead:
            self._dead = True
            parts["death"] += c.death


DEFAULT_CONFIG_V9 = Path(__file__).resolve().parents[2] / "configs" / "reward-v9.yaml"
# The same ledger pays v4-v9: v5 changed stall_restart, v6 adds kill credit in the deriver, v7 adds
# the stagnation cost, v8 shortens the stall limit it is sized for and v9 adds the boss clear
# bonus and potential-based door shaping. Only v7-v9 have a `stagnation` section and only v9 has
# `door_shaping` and `outcome.boss_room_clear_first`; the archived v4-v8 configs stay loadable.
REWARD_V4_VERSIONS = (4, 5, 6, 7, 8, 9)
STAGNATION_VERSIONS = (7, 8, 9)
DOOR_SHAPING_VERSIONS = (9,)
REWARD_V4_COLUMNS = (
    "enemy_damage",
    "room_clear",
    "room_visit",
    "floor_entered",
    "damage_taken",
    "death",
    "time",
    "pickup_coin",
    "pickup_bomb",
    "pickup_key",
    "collectible_new",
    "heal",
    "novelty",
    "stall",
    "stagnation",
    "door_shaping",
)
_V4_SECTIONS: dict[str, tuple[str, ...]] = {
    "outcome": (
        "enemy_hp_fraction_total",
        "room_clear_first",
        "room_first_visit",
        "floor_first_entered",
        "player_damage_half_heart",
        "death",
        "stall_restart",
        "time_second",
    ),
    "pickups": (
        "coin",
        "bomb",
        "key",
        "consumable_run_cap",
        "collectible_new",
        "heal_half_heart",
    ),
    "novelty": ("coefficient", "cell_size"),
}
_STAGNATION_KEYS = ("per_second", "grace_seconds")
_BOSS_KEY = "boss_room_clear_first"
_DOOR_SHAPING_KEYS = ("coefficient",)


@dataclass(frozen=True)
class RewardV4Coefficients:
    enemy_hp_fraction_total: float
    room_clear_first: float
    room_first_visit: float
    floor_first_entered: float
    player_damage_half_heart: float
    death: float
    stall_restart: float
    time_second: float
    coin: float
    bomb: float
    key: float
    consumable_run_cap: float
    collectible_new: float
    heal_half_heart: float
    novelty_coefficient: float
    novelty_cell_size: float
    stagnation_per_second: float = 0.0
    stagnation_grace_seconds: float = 0.0
    boss_room_clear_first: float = 0.0
    door_shaping_coefficient: float = 0.0

    def __post_init__(self) -> None:
        if self.consumable_run_cap < 0 or self.novelty_cell_size <= 0:
            raise ValueError("The consumable cap must be >= 0 and the novelty cell size positive")
        if self.stagnation_grace_seconds < 0:
            raise ValueError("The stagnation grace period must be >= 0")
        if self.door_shaping_coefficient < 0 or self.boss_room_clear_first < 0:
            raise ValueError("The door shaping coefficient and boss clear bonus must be >= 0")

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG_V9) -> Self:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        version = raw.get("reward_version") if isinstance(raw, dict) else None
        sections = dict(_V4_SECTIONS)
        top = {"reward_version", "status", *sections}
        if version in STAGNATION_VERSIONS:
            top.add("stagnation")  # required for v7-v9, forbidden for v4-v6
        if version in DOOR_SHAPING_VERSIONS:
            top.add("door_shaping")  # v9 only
            sections["outcome"] = (*sections["outcome"], _BOSS_KEY)
        if not isinstance(raw, dict) or set(raw) != top or version not in REWARD_V4_VERSIONS:
            raise ValueError(f"Reward v4-v9 configuration must define exactly {sorted(top)}")
        values: dict[str, float] = {}
        for name, keys in sections.items():
            section = raw[name]
            if not isinstance(section, dict) or set(section) != set(keys):
                raise ValueError(f"The {name} section must define exactly {keys}")
            for key in keys:
                value = section[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"{name}.{key} must be a number")
                values[f"novelty_{key}" if name == "novelty" else key] = float(value)
        if "stagnation" in raw:
            section = raw["stagnation"]
            if not isinstance(section, dict) or set(section) != set(_STAGNATION_KEYS):
                raise ValueError(f"The stagnation section must define exactly {_STAGNATION_KEYS}")
            for key in _STAGNATION_KEYS:
                value = section[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"stagnation.{key} must be a number")
                values[f"stagnation_{key}"] = float(value)
        if "door_shaping" in raw:
            section = raw["door_shaping"]
            if not isinstance(section, dict) or set(section) != set(_DOOR_SHAPING_KEYS):
                raise ValueError(
                    f"The door_shaping section must define exactly {_DOOR_SHAPING_KEYS}"
                )
            value = section["coefficient"]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("door_shaping.coefficient must be a number")
            values["door_shaping_coefficient"] = float(value)
        return cls(**values)


@dataclass
class RewardLedgerV4:
    """Outcome-only reward with per-term columns; the sum of the columns is the reward.

    "First" sets, the consumable cap, the heal pool and visited novelty cells belong to a run, so
    they reset only when `begin` sees a new session or game epoch (a new run).

    Door shaping (v9) is potential-based: Phi(s) = -coefficient * d / D with d the distance to the
    nearest open door to an unvisited room and D the room's diagonal; Phi is 0 unless the room is
    clear with no enemies and such a door exists. A step pays gamma * Phi(s') - Phi(s) with
    Phi(s') = 0 after a terminal step. After a room change, Phi(s) is the old room's last value
    and Phi(s') the new room's, as the formula says. `gamma` is the training discount.
    """

    coefficients: RewardV4Coefficients
    stall_seconds: float = DEFAULT_STALL_SECONDS
    gamma: float | None = None
    _stagnation_paid: float = 0.0
    _phi: float = 0.0  # door potential of the previous state
    _run: tuple[str, int] | None = None
    # Room indexes repeat on every floor, so rooms are keyed by (stage, room index).
    _visited: set[tuple[int, int]] = field(default_factory=set)
    _cleared: set[tuple[int, int]] = field(default_factory=set)
    _stages: set[int] = field(default_factory=set)
    _collectibles: set[int] = field(default_factory=set)
    _peak: dict[str, int] = field(default_factory=dict)
    _consumable_paid: float = 0.0
    _lost: float = 0.0  # half-hearts lost and not yet paid back by healing
    _novelty: set[tuple[int, int, int, int]] = field(default_factory=set)
    _initial_hp: dict[tuple[int, int], float] = field(default_factory=dict)
    _removed: dict[tuple[int, int], float] = field(default_factory=dict)
    _damage_fraction: float = 0.0
    _max_stage: int = 0
    _pickups: dict[str, float] = field(default_factory=dict)
    _room: int | None = None
    _stage: int = 0
    _room_type: int = 0
    _dead: bool = False

    def reset(self, episode_id: int) -> None:
        self._dead = False  # run state survives a reset; `begin` decides about a new run

    def begin(
        self,
        frame: EntityFrame,
        room_index: int | None,
        doors: Sequence[OracleDoor] | None = None,
        enemies_present: bool = False,
    ) -> None:
        """Call after every reset with the first frame; a new epoch starts a fresh run."""
        run = (frame.session_id, frame.game_epoch)
        self._room = room_index
        self._stage = frame.room.stage
        self._room_type = frame.room.type
        self._phi = self._potential(frame, doors, enemies_present)  # every episode starts here
        if run == self._run:
            return
        self._run = run
        for seen in (self._visited, self._cleared, self._stages, self._collectibles):
            seen.clear()
        self._novelty.clear()
        for table in (self._peak, self._initial_hp, self._removed):
            table.clear()
        self._consumable_paid = self._lost = self._damage_fraction = 0.0
        self._stagnation_paid = 0.0
        self._max_stage = frame.room.stage
        self._pickups = dict.fromkeys(("coin", "bomb", "key", "collectible"), 0.0)
        # The start room, start floor and starting items are baseline, never rewarded.
        if room_index is not None:
            self._visited.add((self._stage, room_index))
        self._stages.add(frame.room.stage)
        self._collectibles.update(frame.collectibles)
        inventory = frame.inventory
        self._peak.update(coin=inventory.coins, bomb=inventory.bombs, key=inventory.keys)

    def consume(
        self,
        events: Sequence[OracleEvent],
        elapsed_updates: int,
        frame: EntityFrame | None = None,
        room_index: int | None = None,
        doors: Sequence[OracleDoor] | None = None,
        enemies_present: bool = False,
        terminal: bool = False,
    ) -> tuple[float, dict[str, float]]:
        c = self.coefficients
        parts = dict.fromkeys(REWARD_V4_COLUMNS, 0.0)
        if not self._dead:
            parts["time"] = c.time_second * elapsed_updates / UPDATES_PER_SECOND
        if frame is not None:
            self._stage = frame.room.stage  # before events, so room keys use the new floor
            self._room_type = frame.room.type
        for event in events:
            self._apply(event, parts)
        if frame is not None and room_index is not None:
            self._room = room_index
            cell = (
                self._stage,
                room_index,
                math.floor(frame.player_position.x / c.novelty_cell_size),
                math.floor(frame.player_position.y / c.novelty_cell_size),
            )
            if cell not in self._novelty:  # first visit of a cell per run; revisits pay nothing
                self._novelty.add(cell)
                parts["novelty"] = c.novelty_coefficient
        if frame is not None and c.door_shaping_coefficient != 0.0:
            # A terminal step (death, clear, truncation) ends in the zero potential.
            phi = 0.0 if terminal else self._potential(frame, doors, enemies_present)
            parts["door_shaping"] = self._discount() * phi - self._phi
            self._phi = phi
        return sum(parts.values()), parts

    def _discount(self) -> float:
        assert self.gamma is not None  # checked in __post_init__ for a shaping config
        return self.gamma

    def _potential(
        self, frame: EntityFrame, doors: Sequence[OracleDoor] | None, enemies_present: bool
    ) -> float:
        """Phi(s): minus the scaled distance to the nearest open door to an unvisited room.

        Zero without doors data, with a dead player, an unclear room or enemies present, and
        when no open door leads to an unvisited room.
        """
        coefficient = self.coefficients.door_shaping_coefficient
        if coefficient == 0.0 or self._dead or doors is None:
            return 0.0
        if enemies_present or not frame.room.clear:
            return 0.0
        position = frame.player_position
        distances = [
            math.hypot(door.x - position.x, door.y - position.y)
            for door in doors
            if door.open and door.unexplored
        ]
        if not distances:
            return 0.0
        return -coefficient * min(min(distances) / room_diagonal(frame.room.shape), 1.0)

    def stall_restart(self) -> float:
        """Penalty for an episode the watchdog truncated; the env calls it once per episode.

        A dead player was not stalled, so death never pays it.
        """
        return 0.0 if self._dead else self.coefficients.stall_restart

    def __post_init__(self) -> None:
        c = self.coefficients
        if self.stall_seconds <= 0:
            raise ValueError("The stall limit must be positive")
        if c.stagnation_per_second != 0.0 and c.stagnation_grace_seconds >= self.stall_seconds:
            raise ValueError("The stagnation grace period must be shorter than the stall limit")
        if c.door_shaping_coefficient != 0.0 and (self.gamma is None or not 0 < self.gamma <= 1):
            raise ValueError("Door shaping needs the training discount gamma in (0, 1]")

    def stagnation(self, before: float, after: float) -> float:
        """Cost of the idle seconds a step added past the grace period.

        A step whose clock went down (new progress) pays nothing; neither does a dead player.
        """
        c = self.coefficients
        if self._dead or c.stagnation_per_second == 0.0:
            return 0.0
        grace = c.stagnation_grace_seconds
        added = max(0.0, after - grace) - max(0.0, before - grace)
        cost = c.stagnation_per_second * max(0.0, added)
        # One run-wide allowance: clock resets never replenish it, and the last
        # snapshot may overshoot the watchdog limit by part of a step.
        floor = c.stagnation_per_second * max(0.0, self.stall_seconds - grace)
        cost = max(cost, min(0.0, floor - self._stagnation_paid))
        self._stagnation_paid += cost
        return cost

    def run_stats(self) -> dict[str, Any]:
        """Run-level facts for the episode summary."""
        return {
            "damage_dealt_fraction": self._damage_fraction,
            "rooms_visited": len(self._visited),
            "rooms_cleared": len(self._cleared),
            "max_stage": self._max_stage,
            "pickups": dict(self._pickups),
        }

    def _apply(self, event: OracleEvent, parts: dict[str, float]) -> None:
        c = self.coefficients
        enemy: tuple[int, int] | None = None
        if event.entity_id is not None and event.spawn_generation is not None:
            enemy = (event.entity_id, event.spawn_generation)
        kind = event.kind
        if kind == "enemy_spawned" and enemy and event.amount and event.amount > 0:
            self._initial_hp.setdefault(enemy, event.amount)
        elif kind == "enemy_damaged" and enemy and event.amount is not None:
            initial = self._initial_hp.get(enemy)
            if initial is None:
                return  # unknown enemy: no reward without an initial HP
            credited = min(event.amount, initial - self._removed.get(enemy, 0.0))
            if credited > 0:
                self._removed[enemy] = self._removed.get(enemy, 0.0) + credited
                self._damage_fraction += credited / initial
                parts["enemy_damage"] += c.enemy_hp_fraction_total * credited / initial
        elif kind == "room_cleared":
            room = event.room_index if event.room_index is not None else self._room
            if room is not None and (self._stage, room) not in self._cleared:
                self._cleared.add((self._stage, room))
                parts["room_clear"] += c.room_clear_first
                if self._room_type == BOSS_ROOM_TYPE:
                    parts["room_clear"] += c.boss_room_clear_first
        elif kind == "room_entered" and event.room_index is not None:
            self._room = event.room_index
            if (self._stage, event.room_index) not in self._visited:
                self._visited.add((self._stage, event.room_index))
                parts["room_visit"] += c.room_first_visit
        elif kind == "floor_entered" and event.stage is not None:
            self._stage = event.stage
            self._max_stage = max(self._max_stage, event.stage)
            if event.stage not in self._stages:
                self._stages.add(event.stage)
                parts["floor_entered"] += c.floor_first_entered
        elif kind == "player_damaged":
            amount = event.amount or 0.0
            self._lost += amount
            parts["damage_taken"] += c.player_damage_half_heart * amount
        elif kind == "player_healed":
            paid = min(event.amount or 0.0, self._lost)
            self._lost -= paid
            parts["heal"] += c.heal_half_heart * paid
        elif kind == "player_died" and not self._dead:
            self._dead = True
            parts["death"] += c.death
        elif kind == "pickup_gained":
            self._pickup(event, parts)

    def _pickup(self, event: OracleEvent, parts: dict[str, float]) -> None:
        c = self.coefficients
        if event.resource == "collectible" and event.item_id is not None:
            if event.item_id not in self._collectibles:
                self._collectibles.add(event.item_id)
                self._pickups["collectible"] += 1
                parts["collectible_new"] += c.collectible_new
        elif event.resource in ("coin", "bomb", "key") and event.total is not None:
            resource = event.resource
            amount = int(event.amount or 0)
            # Only units above the run's peak count, so drop and re-pickup pays nothing.
            peak = self._peak.get(resource, 0)
            units = max(0, event.total - max(peak, event.total - amount))
            self._peak[resource] = max(peak, event.total)
            self._pickups[resource] += units
            unit_reward: float = getattr(c, resource)
            room_left = max(0.0, c.consumable_run_cap - self._consumable_paid)
            paid = min(units * unit_reward, room_left)
            self._consumable_paid += paid
            parts[f"pickup_{resource}"] += paid
