"""Offline toy room simulator. It is NOT Isaac: it proves plumbing, never game competence.

Coordinates are screen-like (x right, y down). All constants are arbitrary toy values.
"""

import math
import random
import uuid
from dataclasses import dataclass

from .entities import (
    TEAR_FLAG_NAMES,
    WEAPON_NAMES,
    Entity,
    EntityFrame,
    Inventory,
    OracleEvent,
    RoomFacts,
    Stats,
    Vec,
)
from .episodes import ALL_TERMINAL_KINDS, Action, Scenario, StepResult
from .observation import BridgeTimeout, Health

ROOM_W, ROOM_H = 520.0, 280.0
PLAYER_SPEED = 4.0
TEAR_SPEED = 10.0
TEAR_LIFE = 30
FIRE_COOLDOWN = 10
TEAR_DAMAGE = 3.5
TEAR_RADIUS = 14.0
ENEMY_SPEED = 1.2
CONTACT_RADIUS = 22.0
INVULNERABLE_UPDATES = 30
START_HEALTH = 6
MAX_ENEMIES = 16
DIRS = {0: (0.0, 0.0), 1: (-1.0, 0.0), 2: (1.0, 0.0), 3: (0.0, -1.0), 4: (0.0, 1.0)}


@dataclass
class _Enemy:
    entity_id: int
    x: float
    y: float
    hp: float
    max_hp: float
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class _Tear:
    entity_id: int
    x: float
    y: float
    vx: float
    vy: float
    life: int


class SyntheticRoomBackend:
    """Deterministic for a given scenario seed; implements the GameBackend protocol.

    It generates every event itself, so it explicitly declares complete terminal coverage.
    """

    supports_seed = True

    def __init__(self, *, fail_after_updates: int | None = None) -> None:
        self._session = uuid.uuid4().hex
        self._epoch = 0
        self._room_visit = 0
        self._frame = 0
        self._total_updates = 0
        self._fail_after = fail_after_updates
        self.release_calls = 0
        self.closed = False
        self._enemies: list[_Enemy] = []
        self._tears: list[_Tear] = []
        self._next_id = 0
        self._px = self._py = 0.0
        self._pvx = self._pvy = 0.0
        self._red = START_HEALTH
        self._cooldown = 0
        self._invulnerable = 0
        self._finished = False

    def start_episode(self, scenario: Scenario, seed: int | None) -> StepResult:
        if not 0 <= scenario.enemy_count <= MAX_ENEMIES:
            raise ValueError(f"Synthetic room supports 0..{MAX_ENEMIES} enemies")
        rng = random.Random(seed)
        self._epoch += 1
        self._room_visit += 1
        self._frame += 1
        self._px, self._py = ROOM_W / 2, ROOM_H / 2
        self._pvx = self._pvy = 0.0
        self._red, self._cooldown, self._invulnerable = START_HEALTH, 0, 0
        self._tears, self._enemies, self._next_id = [], [], 0
        self._finished = False
        events = []
        for _ in range(scenario.enemy_count):
            while True:
                x, y = rng.uniform(20, ROOM_W - 20), rng.uniform(20, ROOM_H - 20)
                if math.hypot(x - self._px, y - self._py) >= 120.0:
                    break
            enemy = _Enemy(self._new_id(), x, y, scenario.enemy_hp, scenario.enemy_hp)
            self._enemies.append(enemy)
            events.append(self._event("enemy_spawned", entity_id=enemy.entity_id, amount=enemy.hp))
        return StepResult(self._frame_model(), tuple(events), ALL_TERMINAL_KINDS)

    def step(self, action: Action, repeat: int) -> StepResult:
        if self._finished:
            raise RuntimeError("Synthetic episode already ended")
        events: list[OracleEvent] = []
        for _ in range(repeat):
            if self._fail_after is not None and self._total_updates >= self._fail_after:
                raise BridgeTimeout("Injected synthetic transport timeout")
            self._total_updates += 1
            self._update(action, events)
            if self._finished:
                break
        return StepResult(self._frame_model(), tuple(events), ALL_TERMINAL_KINDS)

    def release(self) -> None:
        self.release_calls += 1

    def close(self) -> None:
        self.closed = True

    def _new_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def _event(
        self,
        kind: str,
        *,
        entity_id: int | None = None,
        amount: float | None = None,
        damage_source: str | None = None,
    ) -> OracleEvent:
        return OracleEvent.model_validate(
            {
                "provenance": "synthetic",
                "session_id": self._session,
                "game_epoch": self._epoch,
                "room_visit": self._room_visit,
                "frame_id": self._frame,
                "kind": kind,
                "entity_id": entity_id,
                "spawn_generation": None if entity_id is None else 0,
                "amount": amount,
                "damage_source": damage_source,
            }
        )

    def _update(self, action: Action, events: list[OracleEvent]) -> None:
        self._frame += 1
        mx, my = DIRS[action.move]
        self._pvx, self._pvy = mx * PLAYER_SPEED, my * PLAYER_SPEED
        self._px = min(max(self._px + self._pvx, 0.0), ROOM_W)
        self._py = min(max(self._py + self._pvy, 0.0), ROOM_H)
        self._cooldown = max(0, self._cooldown - 1)
        sx, sy = DIRS[action.shoot]
        if (sx or sy) and self._cooldown == 0:
            speed = (sx * TEAR_SPEED, sy * TEAR_SPEED)
            self._tears.append(_Tear(self._new_id(), self._px, self._py, *speed, TEAR_LIFE))
            self._cooldown = FIRE_COOLDOWN
        self._move_tears(events)
        self._move_enemies(events)
        if self._red <= 0:
            events.append(self._event("player_died"))
            self._finished = True
        elif not self._enemies:
            events.append(self._event("room_cleared"))
            self._finished = True

    def _move_tears(self, events: list[OracleEvent]) -> None:
        alive: list[_Tear] = []
        for tear in self._tears:
            tear.x += tear.vx
            tear.y += tear.vy
            tear.life -= 1
            inside = 0 <= tear.x <= ROOM_W and 0 <= tear.y <= ROOM_H
            hit = next(
                (e for e in self._enemies if math.hypot(e.x - tear.x, e.y - tear.y) < TEAR_RADIUS),
                None,
            )
            if hit is not None:
                dealt = min(TEAR_DAMAGE, hit.hp)
                hit.hp -= dealt
                events.append(self._event("enemy_damaged", entity_id=hit.entity_id, amount=dealt))
                if hit.hp <= 0:
                    self._enemies.remove(hit)
                    events.append(self._event("enemy_killed", entity_id=hit.entity_id))
            elif inside and tear.life > 0:
                alive.append(tear)
        self._tears = alive

    def _move_enemies(self, events: list[OracleEvent]) -> None:
        self._invulnerable = max(0, self._invulnerable - 1)
        for enemy in self._enemies:
            dx, dy = self._px - enemy.x, self._py - enemy.y
            dist = math.hypot(dx, dy) or 1.0
            enemy.vx, enemy.vy = ENEMY_SPEED * dx / dist, ENEMY_SPEED * dy / dist
            enemy.x += enemy.vx
            enemy.y += enemy.vy
            if dist < CONTACT_RADIUS and self._invulnerable == 0 and self._red > 0:
                self._red -= 1
                self._invulnerable = INVULNERABLE_UPDATES
                events.append(self._event("player_damaged", amount=1.0, damage_source="enemy"))

    def _frame_model(self) -> EntityFrame:
        entities = [
            Entity(
                kind="enemy",
                entity_id=e.entity_id,
                spawn_generation=0,
                position=Vec(x=e.x - self._px, y=e.y - self._py),
                velocity=Vec(x=e.vx, y=e.vy),
                hp=e.hp,
                max_hp=e.max_hp,
            )
            for e in self._enemies
        ] + [
            Entity(
                kind="own_attack",
                entity_id=t.entity_id,
                spawn_generation=0,
                position=Vec(x=t.x - self._px, y=t.y - self._py),
                velocity=Vec(x=t.vx, y=t.vy),
            )
            for t in self._tears
        ]
        return EntityFrame(
            provenance="synthetic",
            session_id=self._session,
            game_epoch=self._epoch,
            room_visit=self._room_visit,
            frame_id=self._frame,
            player_position=Vec(x=self._px, y=self._py),
            player_velocity=Vec(x=self._pvx, y=self._pvy),
            health=Health(
                red_half_hearts=max(self._red, 0),
                max_red_half_hearts=START_HEALTH,
                soul_half_hearts=0,
                bone_containers=0,
            ),
            entities=entities,
            inventory=Inventory(
                coins=0,
                bombs=0,
                keys=0,
                active_item=0,
                active_charge=0,
                active_max_charge=0,
                card=0,
                pill=0,
                trinket=0,
            ),
            stats=Stats(
                damage=3.5,
                tears_per_second=2.73,
                range=260.0,
                shot_speed=1.0,
                move_speed=1.0,
                luck=0.0,
            ),
            tear_flags=[False] * len(TEAR_FLAG_NAMES),
            weapons=[name == "tears" for name in WEAPON_NAMES],
            collectibles=[],
            collectible_overflow=0,
            room=RoomFacts(
                type=1,
                stage=1,
                stage_type=0,
                clear=not self._enemies,
                doors=[False] * 8,
            ),
        )
