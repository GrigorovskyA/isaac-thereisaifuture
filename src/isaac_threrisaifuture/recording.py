"""JSON-lines frame recorder/replayer. Policy frames and oracle events never share a file."""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, Any, BinaryIO, Literal, Self

from pydantic import Field, ValidationError, model_validator

from .entities import (
    MAX_FRAME_BYTES,
    OBSERVATION_SCHEMA_VERSION,
    EntityFrame,
    NativeOracleKind,
    OracleEvent,
)
from .native_events import NativeOracleEvent
from .observation import ProtocolError, WireModel, decode

Stream = Literal["policy_frames", "oracle_events", "native_oracle_events"]
Record = EntityFrame | OracleEvent | NativeOracleEvent
_MODELS: dict[Stream, type[Record]] = {
    "policy_frames": EntityFrame,
    "oracle_events": OracleEvent,
    "native_oracle_events": NativeOracleEvent,
}


class RecordingManifest(WireModel):
    type: Literal["recording_manifest"] = "recording_manifest"
    observation_schema_version: int
    stream: Stream
    provenance: Literal["synthetic", "game_api"]
    # The kinds requested when a native recording was created; not producer coverage or delivery.
    # Absent (None) means unknown for a legacy native manifest; [] means none were requested.
    native_oracle_kinds: Annotated[tuple[NativeOracleKind, ...], Field(strict=False)] | None = None

    @model_validator(mode="after")
    def kinds_are_explicit_native_metadata(self) -> Self:
        present = "native_oracle_kinds" in self.model_fields_set
        if present and (self.native_oracle_kinds is None or self.stream != "native_oracle_events"):
            raise ValueError("native_oracle_kinds is a native_oracle_events list or absent")
        if self.native_oracle_kinds is not None and (
            len(set(self.native_oracle_kinds)) != len(self.native_oracle_kinds)
        ):
            raise ValueError("native_oracle_kinds must be unique")
        return self


class JsonlRecorder:
    """Append-only; each record is flushed so a crash keeps every completed line."""

    def __init__(
        self,
        path: Path,
        stream: Stream,
        provenance: Literal["synthetic", "game_api"],
        *,
        native_oracle_kinds: tuple[NativeOracleKind, ...] | None = None,
    ) -> None:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite recording: {path}")
        if native_oracle_kinds is None:
            if stream == "native_oracle_events":
                raise ProtocolError("A native_oracle_events recording needs its requested kinds")
            extra: dict[str, Any] = {}
        elif type(native_oracle_kinds) is not tuple:
            raise ProtocolError("Requested oracle kinds must be a tuple")
        else:
            extra = {"native_oracle_kinds": native_oracle_kinds}
        try:
            manifest = RecordingManifest(
                observation_schema_version=OBSERVATION_SCHEMA_VERSION,
                stream=stream,
                provenance=provenance,
                **extra,
            )
        except ValidationError as exc:
            raise ProtocolError("Invalid recording manifest") from exc
        self._stream = stream
        self._provenance = provenance
        self._kinds = manifest.native_oracle_kinds
        self._file = path.open("x", encoding="utf-8", newline="\n")
        self._write(manifest.model_dump_json(exclude_none=True))

    def _write(self, line: str) -> None:
        if len(line.encode("utf-8")) > MAX_FRAME_BYTES:
            raise ProtocolError("Recording record exceeds size limit")
        self._file.write(line + "\n")
        self._file.flush()

    def record(self, item: Record) -> None:
        if type(item) is not _MODELS[self._stream]:
            raise ProtocolError(f"A {self._stream} recording cannot hold {type(item).__name__}")
        if item.provenance != self._provenance:
            raise ProtocolError("Record provenance differs from the manifest")
        if isinstance(item, NativeOracleEvent) and item.event.kind not in (self._kinds or ()):
            raise ProtocolError("Native oracle event kind is outside the manifest kinds")
        self._write(item.model_dump_json())

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _read_record(handle: BinaryIO) -> bytes:
    raw = handle.readline(MAX_FRAME_BYTES + 2)
    if len(raw.rstrip(b"\n")) > MAX_FRAME_BYTES:
        raise ProtocolError("Recording record exceeds size limit")
    if raw and not raw.rstrip(b"\n"):
        raise ProtocolError("Empty recording record")
    return raw.rstrip(b"\n")


def open_replay(path: Path, stream: Stream) -> tuple[RecordingManifest, Iterator[Record]]:
    """Validate the manifest eagerly so an incompatible file yields no records."""
    with path.open("rb") as handle:
        first = _read_record(handle)
    manifest = decode(first, RecordingManifest, MAX_FRAME_BYTES)
    if manifest.observation_schema_version != OBSERVATION_SCHEMA_VERSION:
        raise ProtocolError(
            f"Unsupported observation schema version {manifest.observation_schema_version}"
        )
    if manifest.stream != stream:
        raise ProtocolError(f"Expected a {stream} recording, found {manifest.stream}")
    model = _MODELS[stream]
    kinds = manifest.native_oracle_kinds

    def records() -> Iterator[Record]:
        with path.open("rb") as handle:
            _read_record(handle)
            while raw := _read_record(handle):
                item = decode(raw, model, MAX_FRAME_BYTES)
                if item.provenance != manifest.provenance:
                    raise ProtocolError("Record provenance differs from the manifest")
                if (
                    kinds is not None
                    and isinstance(item, NativeOracleEvent)
                    and item.event.kind not in kinds
                ):
                    raise ProtocolError("Native oracle event kind is outside the manifest kinds")
                yield item

    return manifest, records()
