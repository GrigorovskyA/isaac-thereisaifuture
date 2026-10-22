"""Progression ledger and goal selection tests (synthetic goals only, not real Isaac unlocks)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from isaac_threrisaifuture.progression import (
    GraphError,
    Ledger,
    LedgerError,
    load_graph,
    select_next_goal,
)

# Synthetic fixture: goal names and edges are invented for tests.
GRAPH = {
    "schema_version": 1,
    "target": "final",
    "goals": {
        "final": {"requires": ["mid_b", "mid_a"]},
        "mid_a": {"requires": ["base"]},
        "mid_b": {"requires": ["base"]},
        "base": {"requires": []},
        "unrelated": {"requires": []},
    },
}


def graph_file(tmp_path: Path, data: object = GRAPH) -> Path:
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def add(ledger: Ledger, goal: str, source: str = "observed_in_game") -> None:
    ledger.append(goal, source, "s1", "r1", "2026-10-17T00:00:00Z")


def test_selection_is_deterministic_and_explained(tmp_path: Path) -> None:
    graph = load_graph(graph_file(tmp_path))
    ledger = Ledger(tmp_path / "ledger.jsonl")
    first = select_next_goal(graph, ledger)
    assert first.goal == "base"
    assert "unrelated" not in first.remaining
    assert first == select_next_goal(graph, Ledger(tmp_path / "ledger.jsonl"))
    add(ledger, "base")
    second = select_next_goal(graph, Ledger(tmp_path / "ledger.jsonl"))
    assert second.goal == "mid_a"
    assert "achievable" in second.reason


def test_non_observed_evidence_is_ignored(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    add(ledger, "base", "manual_note")
    add(ledger, "mid_a", "inferred")
    assert ledger.completed_goals() == frozenset()
    assert select_next_goal(load_graph(graph_file(tmp_path)), ledger).goal == "base"


def test_target_complete(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    add(ledger, "final")
    result = select_next_goal(load_graph(graph_file(tmp_path)), ledger)
    assert result.goal is None and result.remaining == ()


def test_persists_across_reload(tmp_path: Path) -> None:
    add(Ledger(tmp_path / "ledger.jsonl"), "base")
    assert Ledger(tmp_path / "ledger.jsonl").completed_goals() == {"base"}


def test_tampering_is_detected_and_goals_not_counted(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    ledger = Ledger(path)
    add(ledger, "base", "manual_note")
    add(ledger, "mid_a")
    path.write_text(path.read_text().replace("manual_note", "observed_in_game"), encoding="utf-8")
    tampered = Ledger(path)
    assert not tampered.verified
    with pytest.raises(LedgerError):
        tampered.completed_goals()
    with pytest.raises(LedgerError):
        select_next_goal(load_graph(graph_file(tmp_path)), tampered)
    with pytest.raises(LedgerError):
        add(tampered, "final")


def test_deleted_line_breaks_chain(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    ledger = Ledger(path)
    for goal in ("base", "mid_a", "mid_b"):
        add(ledger, goal)
    lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n", encoding="utf-8")
    assert not Ledger(path).verified


def test_missing_dependency_rejected(tmp_path: Path) -> None:
    data = {**GRAPH, "goals": {**GRAPH["goals"], "base": {"requires": ["ghost"]}}}
    with pytest.raises(GraphError, match="missing dependency"):
        load_graph(graph_file(tmp_path, data))


def test_cycle_rejected(tmp_path: Path) -> None:
    data = {**GRAPH, "goals": {**GRAPH["goals"], "base": {"requires": ["final"]}}}
    with pytest.raises(GraphError, match="cycle"):
        load_graph(graph_file(tmp_path, data))
