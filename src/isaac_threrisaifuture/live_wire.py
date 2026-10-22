"""Wire models of the live loop: snapshots with an oracle block and command acks."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .entities import EntitySnapshot
from .observation import Counter, SessionId, WireModel

CommandKind = Literal["action", "heartbeat", "release", "restart"]
MAX_ORACLE_ENEMIES = 64


class OracleEnemy(WireModel):
    entity_id: Counter
    hp: Annotated[float, Field(ge=0, le=1e6)]
    max_hp: Annotated[float, Field(gt=0, le=1e6)]

    @model_validator(mode="after")
    def hp_bounded(self) -> Self:
        if self.hp > self.max_hp:
            raise ValueError("Oracle hp cannot exceed max_hp")
        return self


class LiveOracle(WireModel):
    """Reward/evaluation labels. Never an input of the encoder, policy or normalizer."""

    room_clear: bool
    player_dead: bool
    enemies: Annotated[list[OracleEnemy], Field(max_length=MAX_ORACLE_ENEMIES)]
    enemy_overflow: Counter
    # Level room index for reward and novelty keys. Special rooms use negative indexes.
    room_index: Annotated[int, Field(ge=-64, le=255)]


class LiveSnapshot(EntitySnapshot):
    oracle: LiveOracle | None

    @model_validator(mode="after")
    def oracle_matches_status(self) -> Self:
        if (self.status == "unavailable") != (self.oracle is None):
            raise ValueError("Live oracle must accompany exactly the available snapshots")
        return self


class LiveCommandAck(WireModel):
    type: Literal["command_ack"]
    protocol_version: Literal[1]
    session_id: SessionId
    sequence: Counter
    game_epoch: Counter
    room_visit: Counter
    frame_id: Counter
    kind: CommandKind
    status: Literal["accepted", "rejected"]
