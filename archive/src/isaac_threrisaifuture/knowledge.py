"""Optional, versioned reference knowledge about items. Never holds seed or hidden state."""

import datetime
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

KNOWLEDGE_SCHEMA_VERSION = 1
MAX_KNOWLEDGE_BYTES = 1_048_576
TAG_SATURATION = 4
Text = Annotated[str, Field(min_length=1, max_length=256)]
ItemId = Annotated[str, Field(pattern=r"^[a-z0-9_:.-]{1,64}$")]
Tag = Annotated[str, Field(pattern=r"^[a-z0-9_]{1,48}$")]


class KnowledgeError(Exception):
    """Reference data is malformed, unlicensed, unsafe to load or inconsistent."""


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")


class Source(_Model):
    name: Text
    url: Text | None = None
    commit: Text | None = None
    license: Text
    retrieved: datetime.date
    permitted_use: Text

    @model_validator(mode="after")
    def _locatable(self) -> Self:
        if self.url is None and self.commit is None:
            raise ValueError("source needs a url or a commit")
        return self


class ItemRecord(_Model):
    item_id: ItemId
    kind: Literal["passive", "active", "trinket", "consumable", "card", "pill"]
    source: Text
    tags: tuple[Tag, ...] = ()
    effects: dict[Tag, float] = Field(default_factory=dict)
    unknown_fields: tuple[Tag, ...] = ()
    confidence: Literal["unknown", "low", "medium", "high"] = "unknown"
    verified_in_game: bool = False

    @model_validator(mode="after")
    def _verified_has_confidence(self) -> Self:
        if self.verified_in_game and self.confidence == "unknown":
            raise ValueError("verified_in_game requires a known confidence")
        return self


class KnowledgeDataset(_Model):
    schema_version: int
    synthetic: bool
    tag_vocabulary: tuple[Tag, ...] = Field(min_length=1, max_length=256)
    sources: tuple[Source, ...] = Field(min_length=1)
    items: tuple[ItemRecord, ...]

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.schema_version != KNOWLEDGE_SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {self.schema_version}")
        names = [s.name for s in self.sources]
        if len(set(names)) != len(names):
            raise ValueError("duplicate source names")
        ids = [i.item_id for i in self.items]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate item_id")
        if len(set(self.tag_vocabulary)) != len(self.tag_vocabulary):
            raise ValueError("duplicate tag in tag_vocabulary")
        vocab = set(self.tag_vocabulary)
        for item in self.items:
            if item.source not in names:
                raise ValueError(f"item {item.item_id} cites unknown source {item.source}")
            if not set(item.tags) <= vocab:
                raise ValueError(f"item {item.item_id} uses tags outside tag_vocabulary")
        return self


class KnowledgeBase:
    """Read-only lookup built once at startup; never re-read per policy step."""

    def __init__(self, dataset: KnowledgeDataset | None = None) -> None:
        self._dataset = dataset
        items = dataset.items if dataset else ()
        self._by_id = {i.item_id: i for i in items}
        self.tag_vocabulary: tuple[str, ...] = dataset.tag_vocabulary if dataset else ()

    @property
    def empty(self) -> bool:
        return self._dataset is None

    @property
    def synthetic(self) -> bool:
        return self._dataset is not None and self._dataset.synthetic

    @property
    def vector_size(self) -> int:
        """Tag slots plus one trailing slot for the unknown-item fraction."""
        return len(self.tag_vocabulary) + 1

    def get(self, item_id: str) -> ItemRecord | None:
        return self._by_id.get(item_id)

    def by_tag(self, tag: str) -> tuple[ItemRecord, ...]:
        return tuple(i for i in self._by_id.values() if tag in i.tags)

    def encode(self, owned_item_ids: Sequence[str]) -> list[float]:
        """Fixed-size features from the player's own item ids; unknown ids are only counted."""
        counts = [0] * len(self.tag_vocabulary)
        unknown = 0
        index = {t: n for n, t in enumerate(self.tag_vocabulary)}
        for item_id in owned_item_ids:
            record = self._by_id.get(item_id)
            if record is None:
                unknown += 1
                continue
            for tag in record.tags:
                counts[index[tag]] += 1
        total = len(owned_item_ids)
        features = [min(c, TAG_SATURATION) / TAG_SATURATION for c in counts]
        return [*features, unknown / total if total else 0.0]


def load_knowledge(path: Path) -> KnowledgeBase:
    """Return an empty knowledge base when the file is absent; reject anything invalid."""
    if not path.is_file():
        return KnowledgeBase()
    if path.stat().st_size > MAX_KNOWLEDGE_BYTES:
        raise KnowledgeError(f"{path} exceeds {MAX_KNOWLEDGE_BYTES} bytes")
    try:
        return KnowledgeBase(KnowledgeDataset.model_validate_json(path.read_bytes()))
    except ValidationError as error:
        raise KnowledgeError(f"invalid knowledge file {path}: {error}") from error
