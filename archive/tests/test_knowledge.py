import json
from pathlib import Path
from typing import Any

import pytest

from isaac_threrisaifuture.knowledge import (
    MAX_KNOWLEDGE_BYTES,
    KnowledgeError,
    load_knowledge,
)

FIXTURE = Path(__file__).parent.parent / "data" / "knowledge" / "synthetic_items.json"


def _write(tmp_path: Path, mutate: Any) -> Path:
    data = json.loads(FIXTURE.read_text())
    mutate(data)
    path = tmp_path / "k.json"
    path.write_text(json.dumps(data))
    return path


def test_fixture_loads_and_looks_up() -> None:
    kb = load_knowledge(FIXTURE)
    assert kb.synthetic and not kb.empty
    record = kb.get("fake:0002")
    assert record is not None and not record.verified_in_game
    assert [r.item_id for r in kb.by_tag("synthetic_damage")] == ["fake:0001"]
    assert kb.get("fake:9999") is None


def test_absent_file_gives_empty_knowledge(tmp_path: Path) -> None:
    kb = load_knowledge(tmp_path / "missing.json")
    assert kb.empty and kb.get("fake:0001") is None
    assert kb.encode(["fake:0001"]) == [1.0]


def test_encoder_fixed_size_and_unknown_fraction() -> None:
    kb = load_knowledge(FIXTURE)
    assert kb.encode([]) == [0.0] * kb.vector_size
    vector = kb.encode(["fake:0001", "fake:0001", "nope"])
    assert len(vector) == kb.vector_size == 4
    assert vector[:3] == [0.5, 0.0, 0.0]
    assert vector[3] == pytest.approx(1 / 3)


def _drop_license(d: dict[str, Any]) -> None:
    del d["sources"][0]["license"]


def _drop_locator(d: dict[str, Any]) -> None:
    del d["sources"][0]["url"]


def _duplicate(d: dict[str, Any]) -> None:
    d["items"].append(dict(d["items"][0]))


def _bad_version(d: dict[str, Any]) -> None:
    d["schema_version"] = 2


def _unknown_source(d: dict[str, Any]) -> None:
    d["items"][0]["source"] = "other"


def _unknown_tag(d: dict[str, Any]) -> None:
    d["items"][0]["tags"] = ["not_in_vocabulary"]


def _hidden_field(d: dict[str, Any]) -> None:
    d["items"][0]["seed_contents"] = ["x"]


def _verified_unknown(d: dict[str, Any]) -> None:
    d["items"][1]["verified_in_game"] = True


@pytest.mark.parametrize(
    "mutate",
    [
        _drop_license,
        _drop_locator,
        _duplicate,
        _bad_version,
        _unknown_source,
        _unknown_tag,
        _hidden_field,
        _verified_unknown,
    ],
)
def test_invalid_datasets_are_rejected(tmp_path: Path, mutate: Any) -> None:
    with pytest.raises(KnowledgeError):
        load_knowledge(_write(tmp_path, mutate))


def test_oversized_and_malformed_files_are_rejected(tmp_path: Path) -> None:
    big = tmp_path / "big.json"
    big.write_bytes(b" " * (MAX_KNOWLEDGE_BYTES + 1))
    with pytest.raises(KnowledgeError):
        load_knowledge(big)
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(KnowledgeError):
        load_knowledge(bad)
