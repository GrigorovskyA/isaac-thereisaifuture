"""Policy-visible cardinal firing proxies; not hits, rewards or an action selector."""

import math
from dataclasses import dataclass

from .combat_diagnostics import SHOOT_VECTORS
from .encoding import CAPACITY
from .entities import EntityFrame
from .policy_geometry import CombatGeometry


@dataclass(frozen=True)
class DirectionEvidence:
    clear: tuple[int, ...] = ()
    blocked: tuple[int, ...] = ()
    unknown: tuple[int, ...] = ()
    out_of_range: tuple[int, ...] = ()


@dataclass(frozen=True)
class ShotEvidence:
    supported_weapon: bool
    complete_visible_set: bool
    visible_enemies: int
    directions: tuple[DirectionEvidence, ...]  # left,right,up,down
    axis_tolerance: float

    @property
    def clear_directions(self) -> tuple[int, ...]:
        return tuple(i + 1 for i, d in enumerate(self.directions) if d.clear)

    def classify(self, shoot: int) -> str:
        if type(shoot) is not int or not 0 <= shoot <= 4:
            raise ValueError("Shooting index must be an integer in0..4")
        if not self.supported_weapon:
            return "unknown_weapon"
        if shoot == 0:
            return "missed_clear_opportunity" if self.clear_directions else "no_shoot"
        chosen = self.directions[shoot - 1]
        if chosen.clear:
            return "selected_clear_proxy"
        if self.clear_directions:
            return "wrong_direction_with_clear_opportunity"
        if chosen.unknown:
            return "unknown_selected_line"
        if not self.complete_visible_set:
            return "incomplete_visible_set"
        if chosen.blocked:
            return "only_blocked_selected_direction"
        if chosen.out_of_range:
            return "aligned_out_of_range"
        return "no_aligned_target" if self.visible_enemies else "no_visible_enemy"


def shot_evidence(
    frame: EntityFrame, geometry: CombatGeometry | None, *, axis_tolerance: float = 8.0
) -> ShotEvidence:
    """Bounded pure classification of measured center lines, never oracle state."""
    if not isinstance(frame, EntityFrame):
        raise TypeError("Shot diagnostics require a validated policy EntityFrame")
    if not math.isfinite(axis_tolerance) or not 0 <= axis_tolerance <= 20:
        raise ValueError("Axis tolerance must be finite in0..20worldunits")
    visible = sorted(
        (e for e in frame.entities if e.kind == "enemy"),
        key=lambda e: (e.position.x**2 + e.position.y**2, e.spawn_generation, e.entity_id),
    )
    enemies = visible[: CAPACITY["enemy"]]
    complete = frame.source_overflow.get("enemy", 0) == 0 and len(visible) <= len(enemies)
    empty = tuple(DirectionEvidence() for _ in range(4))
    if geometry is None:
        return ShotEvidence(False, complete, len(enemies), empty, axis_tolerance)
    lines = {e.entity_id: e.clear for e in geometry.enemies}
    if geometry.frame_id != frame.frame_id or not set(lines).issubset(
        {e.entity_id for e in visible}
    ):
        raise ValueError("Shot geometry disagrees with visible frame identity")
    if geometry.weapon != "plain_tears" or geometry.tear_range is None:
        return ShotEvidence(False, complete, len(enemies), empty, axis_tolerance)
    directions = []
    for sx, sy in SHOOT_VECTORS[1:]:
        groups: dict[str, list[int]] = {
            k: [] for k in ("clear", "blocked", "unknown", "out_of_range")
        }
        for enemy in enemies:
            x, y = enemy.position.x, enemy.position.y
            forward, transverse = x * sx + y * sy, abs(x * sy - y * sx)
            if forward <= 0 or transverse > axis_tolerance:
                continue
            if math.hypot(x, y) > geometry.tear_range:
                label = "out_of_range"
            else:
                line = lines.get(enemy.entity_id)
                label = "unknown" if line is None else ("clear" if line else "blocked")
            groups[label].append(enemy.entity_id)
        directions.append(DirectionEvidence(**{k: tuple(v) for k, v in groups.items()}))
    return ShotEvidence(True, complete, len(enemies), tuple(directions), axis_tolerance)
