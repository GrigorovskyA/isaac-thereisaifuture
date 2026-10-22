"""Resource accounting, build-decision interface and counterfactual build evaluation.

Offline contract: shaping is bounded, paid once per entity or item, and never paid for
empty ability use, spending, healed-HP reuse or drop-and-repick loops.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Literal, Protocol

RESOURCE_SCHEMA_VERSION = 1
Resource = Literal["coins", "bombs", "keys", "hearts", "item"]
EventKind = Literal["pickup", "drop", "spend", "use", "damage"]
COUNTABLE = ("coins", "bombs", "keys", "hearts")


@dataclass(frozen=True)
class ResourceState:
    coins: int = 0
    bombs: int = 0
    keys: int = 0
    hearts: float = 0.0
    max_hearts: float = 0.0
    inventory: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ResourceEvent:
    kind: EventKind
    session_id: str
    room_visit: int
    entity_id: int
    spawn_generation: int
    resource: Resource
    amount: float = 1.0
    item_id: str | None = None
    frame_id: int = 0

    @property
    def identity(self) -> tuple[str, int, int, int]:
        return (self.session_id, self.room_visit, self.entity_id, self.spawn_generation)


@dataclass(frozen=True)
class ResourceCoefficients:
    weights: Mapping[str, float] = field(
        default_factory=lambda: {
            "coins": 0.01,
            "bombs": 0.05,
            "keys": 0.05,
            "hearts": 0.1,
            "item": 0.5,
        }
    )
    episode_cap: float = 5.0  # total shaping per episode, bounds any farming loop


@dataclass
class ResourceStats:
    empty_uses: int = 0
    spent: float = 0.0
    ignored_duplicates: int = 0


class ResourceLedger:
    def __init__(self, coefficients: ResourceCoefficients | None = None) -> None:
        self._coef = coefficients or ResourceCoefficients()
        self.reset("")

    def reset(self, session_id: str, state: ResourceState | None = None) -> None:
        self.session_id = session_id
        self.state = state or ResourceState()
        self.stats = ResourceStats()
        self.total = 0.0
        self._paid_entities: set[tuple[str, int, int, int]] = set()
        self._paid_items: set[str] = set()

    def consume(self, events: Sequence[ResourceEvent]) -> float:
        """Apply events in order and return the bounded shaping reward."""
        reward = 0.0
        for e in events:
            if e.session_id != self.session_id:
                raise ValueError(f"event session {e.session_id!r} != ledger {self.session_id!r}")
            reward += self._apply(e)
        paid = max(min(reward, self._coef.episode_cap - self.total), 0.0)
        self.total += paid
        return paid

    def _apply(self, e: ResourceEvent) -> float:
        s = self.state
        if e.kind == "drop":
            if e.item_id is not None:
                self.state = replace(s, inventory=s.inventory - {e.item_id})
            return 0.0
        if e.kind == "use":
            if e.amount <= 0:
                self.stats.empty_uses += 1
            return 0.0  # ability use is never rewarded directly
        if e.kind == "spend":
            self._add(e.resource, -e.amount)
            self.stats.spent += e.amount
            return 0.0
        if e.kind == "damage":
            self._add("hearts", -e.amount)
            return 0.0
        return self._pickup(e)

    def _pickup(self, e: ResourceEvent) -> float:
        first_entity = e.identity not in self._paid_entities
        self._paid_entities.add(e.identity)
        if e.resource == "item":
            if e.item_id is None:
                raise ValueError("item pickup requires item_id")
            known = e.item_id in self._paid_items
            self._paid_items.add(e.item_id)
            self.state = replace(self.state, inventory=self.state.inventory | {e.item_id})
            if known or not first_entity:
                self.stats.ignored_duplicates += 1
                return 0.0
            return self._coef.weights.get("item", 0.0)
        gained = self._add(e.resource, e.amount)  # effective gain only (hearts capped at max)
        if not first_entity:
            self.stats.ignored_duplicates += 1
            return 0.0
        return self._coef.weights.get(e.resource, 0.0) * gained

    def _add(self, resource: str, delta: float) -> float:
        s = self.state
        if resource not in COUNTABLE:
            raise ValueError(f"unsupported resource {resource!r}")
        if resource == "hearts":
            new = min(max(s.hearts + delta, 0.0), s.max_hearts)
            self.state = replace(s, hearts=new)
            return new - s.hearts
        new_i = max(getattr(s, resource) + int(delta), 0)
        self.state = replace(s, **{resource: new_i})
        return float(new_i - getattr(s, resource))


@dataclass(frozen=True)
class Offer:
    entity_id: int
    item_id: str
    price: int = 0


class BuildChooser(Protocol):
    def choose(self, state: ResourceState, offers: Sequence[Offer]) -> int:
        """Return the index of the chosen offer, or -1 to take none."""
        ...


class RandomChooser:
    """Baseline: uniform choice among affordable offers (scripted baseline, not learning)."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def choose(self, state: ResourceState, offers: Sequence[Offer]) -> int:
        ok = [i for i, o in enumerate(offers) if o.price <= state.coins]
        return self._rng.choice(ok) if ok else -1


@dataclass(frozen=True)
class BuildEvaluation:
    build: tuple[str, ...]
    scores: Mapping[str, float]

    @property
    def mean(self) -> float:
        return sum(self.scores.values()) / len(self.scores) if self.scores else 0.0


def evaluate_build(
    build: Sequence[str],
    scenarios: Sequence[str],
    evaluate: Callable[[tuple[str, ...], str], float],
) -> BuildEvaluation:
    """Evaluate a fixed build on fixed scenarios, offline; `evaluate` must not touch a live run."""
    fixed = tuple(build)
    return BuildEvaluation(fixed, {sc: evaluate(fixed, sc) for sc in scenarios})
