"""Offline parser/aggregator for the bounded private `[Isaac Future Trace]` records.

Pure and read-only: it consumes text lines handed over by the caller, never opens files,
never prints or stores raw input, and feeds no policy, reward, normalizer or wire schema.
Rejections carry only fixed category names and line numbers.

The summary is descriptive. It does not infer a maximum firing rate, shot loss, physical
input consumption, or an effect of hold length: tear records are logged for the first four
matching tears per command only, so a missing tear record is not evidence of no shot.
"""

import re
import statistics
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass

PREFIX = "[Isaac Future Trace]"
MAX_RECORD_CHARS = 300  # mod/observer/main.lua TRACE_LINE_MAX
MAX_RECORDS = 512  # mod/observer/main.lua TRACE_MAX_ATTEMPTS, including the stop record
MAX_RAW_LINE_CHARS = 1024  # the prefix must start inside this window of a log line
MAX_SCAN_LINES = 1_000_000
MAX_REJECT_SAMPLES = 16
COOLDOWN_BOUND = 1_000_000.0  # same bound the mod uses before writing "na"
TEARS_LOGGED_PER_COMMAND = 4  # MC_POST_FIRE_TEAR evidence guard: h.tears >= 4
STOP_REASONS = ("count", "deadline", "line_limit", "close")  # close: sparse-mode peer close
BUDGET_STOP_REASONS = frozenset(("count", "deadline", "line_limit"))
LIMITATIONS = (
    "Records are sampled at callback phases; they do not prove engine input consumption "
    "or the engine's internal firing decision.",
    "fire_tear records stop after the first four matching tears per command; a missing "
    "tear record is not evidence that no shot occurred.",
    "No maximum firing rate, shot loss or effect of hold length is inferred; cooldown "
    "ranges are descriptive samples.",
    "A budget stop or a missing stop record leaves the capture incomplete; an explicit close "
    "stop only ends the window and shows neither firing coverage nor physical keyboard "
    "neutrality.",
)

FieldValue = int | float | str | None


class TraceRecordError(ValueError):
    """A prefixed line was rejected; only a fixed category is carried, never input text."""

    def __init__(self, category: str) -> None:
        super().__init__(category)
        self.category = category


@dataclass(frozen=True, slots=True)
class TraceRecord:
    """Validated record. fields holds event-specific values; `na` cooldowns are None."""

    record_id: int
    event: str
    time_ms: int
    frame: int
    update: int
    session: str
    epoch: int
    room: int
    sequence: int | None
    fields: dict[str, FieldValue]


def _match(pattern: re.Pattern[str], value: str, category: str = "malformed") -> str:
    if pattern.fullmatch(value) is None:
        raise TraceRecordError(category)
    return value


_UINT = re.compile(r"[0-9]{1,16}")
_SINT = re.compile(r"-?[0-9]{1,16}")
_WORD = re.compile(r"[A-Za-z0-9_.]{1,32}")
_NUMBER = re.compile(r"-?[0-9]{1,8}(?:\.[0-9]{1,12})?(?:e[+-]?[0-9]{1,3})?")


def _uint(value: str) -> int:
    return int(_match(_UINT, value))


def _sint(value: str) -> int:
    return int(_match(_SINT, value))


def _word(value: str) -> str:
    return _match(_WORD, value)


def _cooldown(value: str) -> float | None:
    if value == "na":
        return None
    number = float(_match(_NUMBER, value, "invalid_cooldown"))
    if not abs(number) <= COOLDOWN_BOUND:  # also rejects nan/inf from overflowing exponents
        raise TraceRecordError("invalid_cooldown")
    return number


def _stop_reason(value: str) -> str:
    if value not in STOP_REASONS:
        raise TraceRecordError("malformed")
    return value


_Parser = Callable[[str], FieldValue]
_COOLDOWNS: dict[str, _Parser] = {"fire_delay": _cooldown, "max_fire_delay": _cooldown}
_SCHEMAS: dict[str, dict[str, _Parser]] = {
    "render_enter": {},
    "render_exit": {},
    "update_enter": {},
    "update_exit": {},
    "new_room": {},
    "new_level": {},
    "pre_game_exit": {},
    "pre_mod_unload": {},
    "game_started": {"continued": _word},
    "game_end": {"game_over": _word},
    "stop": {"reason": _stop_reason},
    "fire_tear": _COOLDOWNS,
    "input": {"hook": _word, "button": _uint, "returned": _word, **_COOLDOWNS},
    "action_accepted": {
        "move": _word,
        "shoot": _word,
        "frames": _uint,
        "until": _uint,
        "deadline_ms": _uint,
    },
    "hold_update": {"hold_seq": _uint, "left": _sint, "upd_since": _uint},
    "release_update": {"hold_seq": _uint, "hold": _word, "upd_since": _uint},
    "release_input": {"hold_seq": _uint, "hook": _uint, "button": _uint, "override": _word},
    "release_superseded": {"hold_seq": _uint, "by_seq": _uint},
}
# The source emits both cooldown fields together or neither (shooting buttons only).
_OPTIONAL = {"input": frozenset(_COOLDOWNS)}
# release/close reason text is free-form: release keeps only a known class, close keeps nothing.
_KNOWN_RELEASE_REASONS = frozenset(
    ("heartbeat", "expiry", "transition", "rejected", "explicit_release", "replaced", "closed")
)
_BOUNDARY_EVENTS = frozenset(
    (
        "new_room",
        "new_level",
        "game_started",
        "game_end",
        "close",
        "pre_game_exit",
        "pre_mod_unload",
    )
)


def _is_boundary(record: TraceRecord) -> bool:
    return record.event in _BOUNDARY_EVENTS or (
        record.event == "stop" and record.fields["reason"] == "close"
    )


_IDENTITY = ("id", "event", "time_ms", "frame", "update", "session", "epoch", "room")
_RECORD = re.compile(
    r" id=(?P<id>[0-9]{1,4}) event=(?P<event>[a-z_]{1,24})(?P<extra>(?: .*)?)"
    r" time_ms=(?P<time_ms>[0-9]{1,16}) frame=(?P<frame>[0-9]{1,16})"
    r" update=(?P<update>[0-9]{1,16}) session=(?P<session>[0-9a-f]{32})"
    r" epoch=(?P<epoch>[0-9]{1,16}) room=(?P<room>[0-9]{1,16})(?: seq=(?P<seq>[0-9]{1,16}))?",
    re.ASCII,
)
_RELEASE = re.compile(
    r" reason=(?P<reason>.{0,40}?) hold_seq=(?P<hold_seq>[0-9]{1,16})"
    r" frame_due=(?P<frame_due>[01]) wall_due=(?P<wall_due>[01])"
    r" left=(?P<left>-?[0-9]{1,16})",
    re.ASCII,
)
_CLOSE = re.compile(r" reason=.{0,60}", re.ASCII)


def _token_fields(event: str, extra: str) -> dict[str, FieldValue]:
    schema = _SCHEMAS[event]
    fields: dict[str, FieldValue] = {}
    for token in extra[1:].split(" ") if extra else ():
        key, _, value = token.partition("=")
        if key in fields or key in _IDENTITY or key == "seq":
            raise TraceRecordError("duplicate_field")
        if key not in schema:
            raise TraceRecordError("unknown_field" if value else "malformed")
        fields[key] = schema[key](value)
    optional = _OPTIONAL.get(event, frozenset())
    if schema.keys() - optional - fields.keys() or len(optional & fields.keys()) not in (
        0,
        len(optional),
    ):
        raise TraceRecordError("missing_field")
    return fields


def _release_fields(extra: str) -> dict[str, FieldValue]:
    match = _RELEASE.fullmatch(extra)
    if match is None:
        raise TraceRecordError("malformed")
    reason = match["reason"]
    return {
        "reason": reason if reason in _KNOWN_RELEASE_REASONS else "other",
        "hold_seq": int(match["hold_seq"]),
        "frame_due": int(match["frame_due"]),
        "wall_due": int(match["wall_due"]),
        "left": int(match["left"]),
    }


def parse_line(line: str) -> TraceRecord | None:
    """Return a record, None for an unrelated line, or raise TraceRecordError."""
    start = line.find(PREFIX, 0, MAX_RAW_LINE_CHARS)
    if start < 0:
        return None
    # Reject by length before any slice copy; two extra chars allow a CRLF line ending.
    if len(line) - start > MAX_RECORD_CHARS + 2:
        raise TraceRecordError("oversized")
    text = line[start:]
    # Only one terminal line ending is framing; spaces, tabs and other whitespace are not.
    if text.endswith("\r\n"):
        text = text[:-2]
    elif text.endswith(("\n", "\r")):
        text = text[:-1]
    if len(text) > MAX_RECORD_CHARS:
        raise TraceRecordError("oversized")
    if not (text.isascii() and text.isprintable()):
        raise TraceRecordError("malformed")
    body = text[len(PREFIX) :]
    counts = {key: body.count(f" {key}=") for key in (*_IDENTITY, "seq")}
    if any(count > 1 for count in counts.values()):
        raise TraceRecordError("duplicate_field")
    if any(counts[key] == 0 for key in _IDENTITY):
        raise TraceRecordError("missing_field")
    match = _RECORD.fullmatch(body)
    if match is None:
        raise TraceRecordError("malformed")
    event, extra = match["event"], match["extra"]
    if event == "release":
        fields = _release_fields(extra)
    elif event == "close":
        if _CLOSE.fullmatch(extra) is None:
            raise TraceRecordError("malformed")
        fields = {}
    elif event in _SCHEMAS:
        fields = _token_fields(event, extra)
    else:
        raise TraceRecordError("unknown_event")
    record_id = int(match["id"])
    sequence = int(match["seq"]) if match["seq"] else None
    if not 1 <= record_id <= MAX_RECORDS or sequence == 0:
        raise TraceRecordError("malformed")
    return TraceRecord(
        record_id=record_id,
        event=event,
        time_ms=int(match["time_ms"]),
        frame=int(match["frame"]),
        update=int(match["update"]),
        session=match["session"],
        epoch=int(match["epoch"]),
        room=int(match["room"]),
        sequence=sequence,
        fields=fields,
    )


@dataclass(frozen=True, slots=True)
class ParsedTrace:
    records: tuple[TraceRecord, ...]
    scanned_lines: int
    trace_lines: int
    rejected: dict[str, int]
    rejected_lines: tuple[tuple[int, str], ...]  # (line number, category), capped
    scan_truncated: bool


def parse_trace(lines: Iterable[str], *, max_lines: int = MAX_SCAN_LINES) -> ParsedTrace:
    """Parse at most max_lines lines (0..MAX_SCAN_LINES); ids are unique and <= MAX_RECORDS."""
    if not 0 <= max_lines <= MAX_SCAN_LINES:
        raise ValueError(f"max_lines must be between 0 and {MAX_SCAN_LINES}")
    records: dict[int, TraceRecord] = {}
    rejected: Counter[str] = Counter()
    samples: list[tuple[int, str]] = []
    scanned = trace_lines = 0
    truncated = False

    def reject(number: int, category: str) -> None:
        rejected[category] += 1
        if len(samples) < MAX_REJECT_SAMPLES:
            samples.append((number, category))

    for number, line in enumerate(lines, 1):
        if number > max_lines:
            truncated = True
            break
        scanned = number
        try:
            if not isinstance(line, str):
                raise TraceRecordError("malformed")
            record = parse_line(line)
        except TraceRecordError as error:
            trace_lines += 1
            reject(number, error.category)
            continue
        if record is None:
            continue
        trace_lines += 1
        if record.record_id in records:
            reject(number, "duplicate_id")
        else:
            records[record.record_id] = record
    return ParsedTrace(
        tuple(records.values()), scanned, trace_lines, dict(rejected), tuple(samples), truncated
    )


@dataclass(frozen=True, slots=True)
class ValueRange:
    """Finite samples only; `na` samples are counted in missing and never become zero."""

    samples: int
    missing: int
    minimum: float | None
    maximum: float | None


@dataclass(frozen=True, slots=True)
class ReleaseInterval:
    """Release to the next accepted action in the same session, epoch and room."""

    session: str
    epoch: int
    release_id: int
    accept_id: int
    hold_sequence: int
    next_sequence: int
    reason: str
    gap_ms: int
    gap_frames: int


@dataclass(frozen=True, slots=True)
class IntervalStats:
    count: int
    minimum_ms: int
    median_ms: float
    maximum_ms: int


@dataclass(frozen=True, slots=True)
class GroupSummary:
    """Records sharing session, epoch and the latest accepted sequence at emission."""

    session: str
    epoch: int
    sequence: int | None
    first_id: int
    last_id: int
    first_time_ms: int
    last_time_ms: int
    first_frame: int
    last_frame: int
    events: dict[str, int]
    move: str | None
    shoot: str | None
    frames: int | None
    tear_log_saturated: bool  # reached the first-four logging limit; later tears are unlogged
    cooldowns: dict[str, ValueRange]


@dataclass(frozen=True, slots=True)
class TraceSummary:
    records: int
    scanned_lines: int
    trace_lines: int
    rejected: dict[str, int]
    rejected_lines: tuple[tuple[int, str], ...]
    stop_reason: str | None
    incomplete: bool
    incomplete_reasons: tuple[str, ...]
    missing_ids: int
    events: dict[str, int]
    shoot_directions: dict[str, int]
    input_phases: dict[str, int]
    cooldowns: dict[str, ValueRange]
    groups: tuple[GroupSummary, ...]
    intervals: tuple[ReleaseInterval, ...]
    interval_stats: IntervalStats | None
    excluded_intervals: int
    unpaired_releases: int
    limitations: tuple[str, ...]


class _Cooldowns:
    def __init__(self) -> None:
        self.values: dict[str, list[float]] = {}
        self.missing: Counter[str] = Counter()

    def add(self, record: TraceRecord) -> None:
        for name in _COOLDOWNS:
            if name not in record.fields:
                continue
            key = f"{record.event}.{name}"
            value = record.fields[name]
            self.values.setdefault(key, [])
            if isinstance(value, float):
                self.values[key].append(value)
            else:
                self.missing[key] += 1

    def ranges(self) -> dict[str, ValueRange]:
        return {
            key: ValueRange(
                len(values),
                self.missing[key],
                min(values) if values else None,
                max(values) if values else None,
            )
            for key, values in sorted(self.values.items())
        }


class _Group:
    def __init__(self, first: TraceRecord) -> None:
        self.first, self.last = first, first
        self.events: Counter[str] = Counter()
        self.accepted: TraceRecord | None = None
        self.cooldowns = _Cooldowns()

    def add(self, record: TraceRecord) -> None:
        self.last = record
        self.events[record.event] += 1
        if record.event == "action_accepted" and self.accepted is None:
            self.accepted = record
        self.cooldowns.add(record)

    def summary(self) -> GroupSummary:
        first, last, accepted = self.first, self.last, self.accepted
        move = accepted.fields["move"] if accepted else None
        shoot = accepted.fields["shoot"] if accepted else None
        frames = accepted.fields["frames"] if accepted else None
        return GroupSummary(
            session=first.session,
            epoch=first.epoch,
            sequence=first.sequence,
            first_id=first.record_id,
            last_id=last.record_id,
            first_time_ms=first.time_ms,
            last_time_ms=last.time_ms,
            first_frame=first.frame,
            last_frame=last.frame,
            events=dict(self.events),
            move=move if isinstance(move, str) else None,
            shoot=shoot if isinstance(shoot, str) else None,
            frames=frames if isinstance(frames, int) else None,
            tear_log_saturated=self.events["fire_tear"] >= TEARS_LOGGED_PER_COMMAND,
            cooldowns=self.cooldowns.ranges(),
        )


def _interval(release: TraceRecord, accept: TraceRecord) -> ReleaseInterval | None:
    hold = release.fields["hold_seq"]
    gap_ms, gap_frames = accept.time_ms - release.time_ms, accept.frame - release.frame
    if (
        not isinstance(hold, int)
        or accept.sequence is None
        or accept.sequence <= hold
        or accept.room != release.room
        or gap_ms < 0
        or gap_frames < 0
    ):
        return None
    reason = release.fields["reason"]
    return ReleaseInterval(
        session=release.session,
        epoch=release.epoch,
        release_id=release.record_id,
        accept_id=accept.record_id,
        hold_sequence=hold,
        next_sequence=accept.sequence,
        reason=reason if isinstance(reason, str) else "other",
        gap_ms=gap_ms,
        gap_frames=gap_frames,
    )


def summarize_trace(parsed: ParsedTrace) -> TraceSummary:
    ordered = sorted(parsed.records, key=lambda record: record.record_id)
    groups: dict[tuple[str, int, int | None], _Group] = {}
    pending: dict[tuple[str, int], TraceRecord] = {}
    intervals: list[ReleaseInterval] = []
    shoot_directions: Counter[str] = Counter()
    input_phases: Counter[str] = Counter()
    cooldowns = _Cooldowns()
    excluded = unpaired = 0
    for record in ordered:
        key = (record.session, record.epoch, record.sequence)
        group = groups.get(key)
        if group is None:
            group = groups[key] = _Group(record)
        group.add(record)
        cooldowns.add(record)
        if record.event == "input":
            input_phases[f"{record.fields['hook']}/{record.fields['returned']}"] += 1
        scope = (record.session, record.epoch)
        if record.event == "release":
            if scope in pending:
                unpaired += 1
            pending[scope] = record
        elif record.event == "action_accepted":
            shoot_directions[str(record.fields["shoot"])] += 1
            release = pending.pop(scope, None)
            if release is not None:
                interval = _interval(release, record)
                if interval is None:
                    excluded += 1
                else:
                    intervals.append(interval)
        elif _is_boundary(record) and pending.pop(scope, None) is not None:
            excluded += 1
    unpaired += len(pending)

    stops = [record for record in ordered if record.event == "stop"]
    stop_reason = str(stops[0].fields["reason"]) if stops else None
    missing_ids = ordered[-1].record_id - len(ordered) if ordered else 0
    reasons = []
    if not stops:
        reasons.append("no_stop_record")
    elif stop_reason in BUDGET_STOP_REASONS:
        reasons.append(f"stopped_by_{stop_reason}")
    if len(stops) > 1:
        reasons.append("multiple_stop_records")
    if stops and ordered[-1] is not stops[0]:
        reasons.append("records_after_stop")
    if parsed.rejected:
        reasons.append("rejected_records")
    if parsed.scan_truncated:
        reasons.append("scan_limit_reached")
    if missing_ids:
        reasons.append("id_gaps")
    gaps = [interval.gap_ms for interval in intervals]
    stats = (
        IntervalStats(len(gaps), min(gaps), statistics.median(gaps), max(gaps)) if gaps else None
    )
    return TraceSummary(
        records=len(ordered),
        scanned_lines=parsed.scanned_lines,
        trace_lines=parsed.trace_lines,
        rejected=dict(parsed.rejected),
        rejected_lines=parsed.rejected_lines,
        stop_reason=stop_reason,
        incomplete=bool(reasons),
        incomplete_reasons=tuple(reasons),
        missing_ids=missing_ids,
        events=dict(Counter(record.event for record in ordered)),
        shoot_directions=dict(shoot_directions),
        input_phases=dict(input_phases),
        cooldowns=cooldowns.ranges(),
        groups=tuple(group.summary() for group in groups.values()),
        intervals=tuple(intervals),
        interval_stats=stats,
        excluded_intervals=excluded,
        unpaired_releases=unpaired,
        limitations=LIMITATIONS,
    )


def analyze_trace(lines: Iterable[str], *, max_lines: int = MAX_SCAN_LINES) -> TraceSummary:
    """Parse and summarize trace lines from any text-line iterable."""
    return summarize_trace(parse_trace(lines, max_lines=max_lines))
