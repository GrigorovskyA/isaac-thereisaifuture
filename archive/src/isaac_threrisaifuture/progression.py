"""Tamper-evident progression ledger and deterministic goal selection (offline contract)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

LEDGER_SCHEMA_VERSION: Final = 1
GRAPH_SCHEMA_VERSION: Final = 1
GENESIS_HASH: Final = "0" * 64
SOURCES: Final = ("observed_in_game", "manual_note", "inferred")
COUNTED_SOURCE: Final = "observed_in_game"


class LedgerError(Exception):
    """Ledger is malformed or fails hash-chain verification."""


class GraphError(Exception):
    """Unlock graph is malformed, has missing dependencies or contains a cycle."""


@dataclass(frozen=True)
class LedgerEvent:
    seq: int
    goal_id: str
    source: str
    session_id: str
    run_id: str
    timestamp: str
    prev_hash: str
    hash: str


def _digest(body: Mapping[str, object]) -> str:
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_FIELDS = ("seq", "goal_id", "source", "session_id", "run_id", "timestamp", "prev_hash")


def _body(event: LedgerEvent) -> dict[str, object]:
    return {"schema": LEDGER_SCHEMA_VERSION, **{f: getattr(event, f) for f in _FIELDS}}


class Ledger:
    """Append-only JSONL ledger; every line chains to the previous via prev_hash."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.events: list[LedgerEvent] = []
        self.error: str | None = None
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        prev = GENESIS_HASH
        for n, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                data = json.loads(line)
                event = LedgerEvent(**{f: data[f] for f in (*_FIELDS, "hash")})
                if data.get("schema") != LEDGER_SCHEMA_VERSION or len(data) != len(_FIELDS) + 2:
                    raise ValueError("schema or unexpected fields")
            except (ValueError, KeyError, TypeError) as exc:
                self.error = f"line {n}: malformed ({exc})"
                return
            if event.seq != n - 1 or event.prev_hash != prev:
                self.error = f"line {n}: broken chain"
                return
            if event.source not in SOURCES or event.hash != _digest(_body(event)):
                self.error = f"line {n}: hash or source invalid"
                return
            self.events.append(event)
            prev = event.hash

    @property
    def verified(self) -> bool:
        return self.error is None

    def append(
        self, goal_id: str, source: str, session_id: str, run_id: str, timestamp: str
    ) -> LedgerEvent:
        if not self.verified:
            raise LedgerError(f"refusing to append to unverified ledger: {self.error}")
        if source not in SOURCES:
            raise ValueError(f"unknown evidence source: {source}")
        prev = self.events[-1].hash if self.events else GENESIS_HASH
        draft = LedgerEvent(
            len(self.events), goal_id, source, session_id, run_id, timestamp, prev, ""
        )
        event = replace(draft, hash=_digest(_body(draft)))
        line = json.dumps({**_body(event), "hash": event.hash}, sort_keys=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        self.events.append(event)
        return event

    def completed_goals(self) -> frozenset[str]:
        """Goals backed by observed_in_game evidence; refuses to count if verification failed."""
        if not self.verified:
            raise LedgerError(f"ledger verification failed: {self.error}")
        return frozenset(e.goal_id for e in self.events if e.source == COUNTED_SOURCE)


@dataclass(frozen=True)
class UnlockGraph:
    target: str
    requires: Mapping[str, tuple[str, ...]]


def load_graph(path: Path) -> UnlockGraph:
    """Load a dependency table supplied as data; never ships real unlock requirements."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["schema_version"] != GRAPH_SCHEMA_VERSION:
            raise GraphError("unsupported graph schema_version")
        requires = {k: tuple(v["requires"]) for k, v in data["goals"].items()}
        target = data["target"]
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise GraphError(f"malformed graph: {exc!r}") from exc
    if target not in requires:
        raise GraphError(f"target {target!r} is not a defined goal")
    for goal, deps in requires.items():
        for dep in deps:
            if dep not in requires:
                raise GraphError(f"goal {goal!r} has missing dependency {dep!r}")
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        if state.get(node) == 1:
            raise GraphError(f"dependency cycle through {node!r}")
        if state.get(node) == 2:
            return
        state[node] = 1
        for dep in sorted(requires[node]):
            visit(dep)
        state[node] = 2

    for goal in sorted(requires):
        visit(goal)
    return UnlockGraph(target, requires)


@dataclass(frozen=True)
class GoalSelection:
    goal: str | None
    reason: str
    remaining: tuple[str, ...]


def select_next_goal(graph: UnlockGraph, ledger: Ledger) -> GoalSelection:
    """Pick the alphabetically first achievable goal among those the target still needs."""
    done = ledger.completed_goals()
    needed: set[str] = set()
    stack = [graph.target]
    while stack:
        goal = stack.pop()
        if goal in done or goal in needed:
            continue
        needed.add(goal)
        stack.extend(graph.requires[goal])
    remaining = tuple(sorted(needed))
    if not remaining:
        return GoalSelection(None, f"target {graph.target!r} has observed evidence", ())
    ready = [g for g in remaining if all(d in done for d in graph.requires[g])]
    goal = ready[0]
    reason = (
        f"{goal!r} is achievable now (requires {sorted(graph.requires[goal]) or 'nothing'}, "
        f"all with observed_in_game evidence); {len(remaining)} goal(s) remain toward "
        f"{graph.target!r}"
    )
    return GoalSelection(goal, reason, remaining)
