"""Versioned read-only wire models. No game API or policy logic lives here."""

import json
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

MAX_MESSAGE_BYTES = 32768
CAPABILITIES = ("snapshot_v1", "availability", "raw_health_v1")
Counter = Annotated[int, Field(ge=0, le=2**53 - 1)]
SessionId = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
Label = Annotated[str, Field(min_length=1, max_length=128)]


class BridgeError(Exception):
    """Observation infrastructure fault, never a game outcome."""


class ProtocolError(BridgeError):
    """Peer violated the versioned read-only contract."""


class BridgeTimeout(BridgeError):
    """A bounded wait expired; game status cannot be inferred."""


class PeerDisconnected(BridgeError):
    """Peer closed before another complete record arrived."""


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)

    @field_validator(
        "protocol_version",
        "schema_version",
        "observation_schema_version",
        "index",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def integer_literals(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("Version and player index must be integers")
        return value


class Hello(WireModel):
    type: Literal["hello"] = "hello"
    protocol_version: Literal[1] = 1
    schema_version: Literal[1] = 1
    session_id: SessionId
    required_capabilities: list[Label]


class GameInfo(WireModel):
    version: Label | None
    steam_build: Label | None
    provenance: Literal["unavailable", "operator_config"]

    @model_validator(mode="after")
    def provenance_matches(self) -> Self:
        available = self.version is not None or self.steam_build is not None
        if available != (self.provenance == "operator_config"):
            raise ValueError("Game metadata needs explicit provenance")
        return self


class HelloAck(WireModel):
    type: Literal["hello_ack"]
    protocol_version: Literal[1]
    schema_version: Literal[1]
    session_id: SessionId
    capabilities: Annotated[list[Label], Field(max_length=16)]
    mod_version: Label
    lua_version: Label
    extender_present: bool
    game: GameInfo


class Position(WireModel):
    x: Annotated[float, Field(ge=-1e6, le=1e6)]
    y: Annotated[float, Field(ge=-1e6, le=1e6)]


class Health(WireModel):
    red_half_hearts: Counter
    max_red_half_hearts: Counter
    soul_half_hearts: Counter
    bone_containers: Counter


class Player(WireModel):
    index: Literal[0]
    character_type: Counter
    position: Position
    health: Health


class Room(WireModel):
    visit_id: Counter


class Snapshot(WireModel):
    type: Literal["snapshot"]
    schema_version: Literal[1]
    session_id: SessionId
    sequence: Counter
    game_epoch: Counter
    frame_id: Counter | None
    update_id: Counter
    status: Literal["active", "paused", "unavailable"]
    reason: Literal["not_in_game", "state_read_failed"] | None
    room: Room | None
    player: Player | None

    @model_validator(mode="after")
    def availability_matches(self) -> Self:
        if self.status == "unavailable":
            if any(v is not None for v in (self.frame_id, self.room, self.player)):
                raise ValueError("Unavailable snapshots cannot expose stale state")
            if self.reason is None:
                raise ValueError("Unavailable snapshots need a reason")
        elif any(v is None for v in (self.frame_id, self.room, self.player)):
            raise ValueError("Available snapshots need frame, room and player")
        elif self.reason is not None:
            raise ValueError("Available snapshots cannot have an unavailable reason")
        return self


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("Duplicate JSON key")
        result[key] = value
    return result


def decode[T: WireModel](raw: bytes, model: type[T], limit: int = MAX_MESSAGE_BYTES) -> T:
    """Validate one bounded JSON record; never return partially valid fields."""
    if not raw or len(raw) > limit or b"\r" in raw or b"\n" in raw:
        raise ProtocolError("Invalid record size or delimiter")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        return model.model_validate(value)
    except (UnicodeError, ValueError, RecursionError, ValidationError) as exc:
        raise ProtocolError(f"Invalid {model.__name__} record") from exc
