"""Behavioral tests for the pure native step lifecycle reducer. All facts are fabricated.

Nothing here proves engine behavior: a READY decision is only a logical consequence of
the supplied facts.
"""

import dataclasses

import pytest
from synthetic import SESSION

from isaac_threrisaifuture.native_protocol import StepCommand
from isaac_threrisaifuture.native_step_lifecycle import (
    MAX_FACTS,
    AcceptanceFact,
    ClockFact,
    ContextChangeFact,
    InterruptFact,
    IntervalFact,
    NativeStepLifecycle,
    ReleaseFact,
    SealFact,
)
from isaac_threrisaifuture.observation import ProtocolError

OTHER = "b" * 32
START, DEADLINE = 1000, 1200
BASE = dict(session_id=SESSION, game_epoch=1, room_visit=1)
IDENT = dict(BASE, sequence=1)


def machine(frames=6, baseline=7, deadline=DEADLINE):
    command = StepCommand(
        session_id=SESSION, sequence=1, game_epoch=1, room_visit=1, frame_id=100, frames=frames
    )
    return NativeStepLifecycle(
        command, baseline_last_event_id=baseline, started_ms=START, deadline_ms=deadline
    )


def ack(at=1010, frame=101, **c):
    return AcceptanceFact(at_ms=at, frame_id=frame, **{**IDENT, **c})


def interval(at=1020, accepted=101, requested=6, elapsed=6, end=107, **c):
    return IntervalFact(
        at_ms=at,
        accepted_frame=accepted,
        requested_updates=requested,
        elapsed_updates=elapsed,
        end_frame=end,
        **{**IDENT, **c},
    )


def release(at=1030, frame=107, **c):
    return ReleaseFact(at_ms=at, frame_id=frame, **{**IDENT, **c})


def seal(at=1040, end=107, wm=9, **c):
    return SealFact(at_ms=at, end_frame=end, last_event_id=wm, **{**BASE, **c})


def interrupt(kind, at=1100, frame=104, **c):
    return InterruptFact(at_ms=at, frame_id=frame, kind=kind, **{**IDENT, **c})


def change(kind, at=1100, frame=104, **c):
    return ContextChangeFact(at_ms=at, frame_id=frame, kind=kind, **{**BASE, **c})


def feed(m, *facts):
    decision = None
    for fact in facts:
        decision = m.submit(fact)
    return decision


FULL = (ack, interval, release, seal)


def test_all_evidence_yields_one_local_candidate():
    m = machine()
    d = feed(m, *(f() for f in FULL))
    assert (d.state, d.fresh, d.missing, d.release_required) == ("ready", True, (), False)
    c = d.candidate
    assert (c.accepted_frame, c.end_frame, c.elapsed_updates, c.last_event_id) == (101, 107, 6, 9)
    assert c.provenance == "local_reducer_unverified"
    again = m.submit(ClockFact(at_ms=1050))
    assert (again.state, again.fresh, again.candidate) == ("ready", False, c)


@pytest.mark.parametrize(
    "order", [(0, 1, 2, 3), (3, 2, 1, 0), (2, 3, 0, 1), (1, 3, 2, 0), (3, 0, 2, 1)]
)
def test_independent_facts_may_arrive_in_any_order(order):
    m = machine()
    d = feed(m, *(FULL[i](at=1010 + 10 * pos) for pos, i in enumerate(order)))
    assert d.state == "ready" and d.candidate.end_frame == 107


@pytest.mark.parametrize("skip", range(4))
def test_any_single_missing_prerequisite_keeps_waiting(skip):
    names = ("acceptance", "interval", "release", "seal")
    d = feed(machine(), *(f() for i, f in enumerate(FULL) if i != skip))
    assert d.state == "waiting" and d.missing == (names[skip],) and d.candidate is None


def test_acceptance_and_clock_alone_never_complete():
    m = machine()
    assert feed(m, ack()).state == "waiting"
    d = m.submit(ClockFact(at_ms=1199))
    assert d.state == "waiting" and d.release_required
    assert m.submit(ClockFact(at_ms=1200)).state == "expired"


@pytest.mark.parametrize("frames", [1, 15])
def test_repeat_bounds(frames):
    m = machine(frames=frames)
    end = 101 + frames
    d = feed(
        m,
        ack(),
        interval(requested=frames, elapsed=frames, end=end),
        release(frame=end),
        seal(end=end),
    )
    assert d.state == "ready" and d.candidate.requested_updates == frames


@pytest.mark.parametrize(
    "bad",
    [
        dict(elapsed=0, end=101),
        dict(elapsed=5, end=106),
        dict(elapsed=7, end=108),
        dict(end=108),  # skipped frame inside the interval
        dict(end=106),
        dict(end=101, elapsed=6),  # regression: end equals accepted
    ],
)
def test_partial_short_long_or_skipped_interval_faults(bad):
    d = feed(machine(), ack(), interval(**bad))
    assert (d.state, d.reason, d.candidate) == ("faulted", "partial_interval", None)


def test_interval_for_other_repeat_count_is_contradictory():
    d = machine(frames=6).submit(interval(requested=5, elapsed=5, end=106))
    assert d.reason == "contradictory_fact"


@pytest.mark.parametrize(
    "fact, reason",
    [
        (lambda: ack(session_id=OTHER), "foreign_context"),
        (lambda: ack(sequence=2), "foreign_context"),
        (lambda: ack(game_epoch=2), "foreign_context"),
        (lambda: ack(room_visit=2), "foreign_context"),
        (lambda: ack(frame=99), "stale_fact"),
        (lambda: ack(frame=116), "contradictory_fact"),
        (lambda: interval(accepted=99, end=105), "stale_fact"),
        (lambda: release(frame=99), "stale_fact"),
        (lambda: release(room_visit=2), "foreign_context"),
        (lambda: seal(session_id=OTHER), "foreign_context"),
        (lambda: seal(room_visit=2), "foreign_context"),
        (lambda: seal(end=99), "stale_fact"),
        (lambda: seal(wm=6), "watermark_regression"),
    ],
)
def test_identity_frame_and_watermark_defects_fault(fact, reason):
    d = machine().submit(fact())
    assert (d.state, d.reason) == ("faulted", reason)


def test_equal_baseline_watermark_is_allowed():
    d = feed(machine(baseline=9), *(f() for f in FULL))
    assert d.state == "ready" and d.candidate.last_event_id == 9


@pytest.mark.parametrize(
    "first, second",
    [
        (ack(), ack(frame=102)),
        (interval(), ack(frame=102)),
        (ack(), interval(accepted=102, end=108)),
        (seal(), seal(wm=10)),
        (seal(at=1010), interval(at=1020, end=108, accepted=102)),
        (release(frame=104), interval()),
        (interval(), release(frame=106)),
        (interval(), seal(end=108)),
        (seal(end=101), ack(at=1050)),
    ],
)
def test_contradictory_evidence_faults_in_any_arrival_order(first, second):
    d = feed(machine(), first, dataclasses.replace(second, at_ms=1100))
    assert (d.state, d.reason) == ("faulted", "contradictory_fact")


def test_identical_duplicates_are_ignored_but_counted():
    m = machine()
    d1 = feed(m, ack(), ack(at=1011), ack(at=1012))
    assert (d1.state, d1.facts_counted, d1.missing) == (
        "waiting",
        3,
        ("interval", "release", "seal"),
    )
    d = feed(m, interval(), release(), seal(), seal(at=1041))
    assert d.state == "ready" and not d.fresh and not d.conflict_after_ready


def test_duplicate_after_ready_cannot_emit_second_candidate():
    m = machine()
    ready = feed(m, *(f() for f in FULL))
    fresh = [m.submit(f(at=1100)) for f in FULL]
    assert ready.fresh and not any(d.fresh for d in fresh)
    assert fresh[-1].candidate == ready.candidate and not fresh[-1].conflict_after_ready


def test_seal_may_precede_or_follow_release_but_must_name_same_endpoint():
    a = feed(machine(), ack(), interval(), seal(), release(at=1050))
    b = feed(machine(), ack(), interval(), release(), seal())
    assert a.state == b.state == "ready"
    d = feed(machine(), ack(), interval(), release(), seal(end=108))
    assert d.reason == "contradictory_fact"


@pytest.mark.parametrize(
    "kind, state, reason",
    [
        ("pause", "cancelled", "pause"),
        ("explicit_release", "cancelled", "explicit_release"),
        ("input_fault", "cancelled", "input_fault"),
        ("death_candidate", "unsupported_terminal", "death_candidate"),
        ("disconnect", "faulted", "disconnect"),
        ("transport_fault", "faulted", "transport_fault"),
        ("authority_lost", "expired", "authority_lost"),
    ],
)
@pytest.mark.parametrize(
    "progress", [(), ("ack",), ("ack", "interval"), ("ack", "interval", "seal")]
)
def test_interrupts_end_a_waiting_step_with_release_still_required(kind, state, reason, progress):
    m = machine()
    made = dict(ack=ack(), interval=interval(), seal=seal())
    feed(m, *(made[p] for p in progress))
    d = m.submit(interrupt(kind, at=1100, frame=107))
    assert (d.state, d.reason, d.fresh) == (state, reason, True)
    assert d.candidate is None and d.release_required


@pytest.mark.parametrize(
    "fact, state, reason",
    [
        (change("room_change", room_visit=2), "cancelled", "transition"),
        (change("floor_change", room_visit=1), "cancelled", "transition"),
        (change("floor_change", room_visit=3), "cancelled", "transition"),
        (change("epoch_change", game_epoch=2), "unsupported_terminal", "epoch_change"),
        (change("session_change", session_id=OTHER), "faulted", "session_changed"),
    ],
)
def test_context_changes_never_complete_or_attach_new_frames(fact, state, reason):
    m = machine()
    feed(m, ack(), interval(), release())
    d = m.submit(fact)
    assert (d.state, d.reason, d.candidate) == (state, reason, None)
    assert (d.session_id, d.game_epoch, d.room_visit) == (SESSION, 1, 1)


@pytest.mark.parametrize(
    "fact, reason",
    [
        (change("room_change"), "contradictory_fact"),
        (change("room_change", room_visit=0, frame=104), "stale_fact"),
        (change("epoch_change"), "contradictory_fact"),
        (change("epoch_change", game_epoch=0), "stale_fact"),
        (change("session_change"), "contradictory_fact"),
        (change("floor_change", session_id=OTHER), "foreign_context"),
        (change("floor_change", game_epoch=2), "foreign_context"),
        (change("room_change", room_visit=2, frame=99), "stale_fact"),
    ],
)
def test_implausible_context_changes_fault(fact, reason):
    d = machine().submit(fact)
    assert (d.state, d.reason) == ("faulted", reason)


def test_hp_zero_or_silence_never_imply_death():
    m = machine()
    d = m.submit(ClockFact(at_ms=1100))
    assert d.state == "waiting"
    d = m.submit(ClockFact(at_ms=1200))
    assert (d.state, d.reason) == ("expired", "wall_deadline")


def test_release_required_until_valid_late_release_without_changing_outcome():
    m = machine()
    cancelled = m.submit(interrupt("pause"))
    assert cancelled.release_required
    m.submit(ClockFact(at_ms=1100))
    wrong = m.submit(release(at=1110, sequence=2))
    assert wrong.release_required
    low = m.submit(release(at=1120, frame=99))
    assert low.release_required
    late = m.submit(release(at=1130, frame=104))
    assert (late.state, late.reason, late.fresh, late.release_required) == (
        "cancelled",
        "pause",
        False,
        False,
    )
    assert late.candidate is None


@pytest.mark.parametrize(
    "stop",
    [
        lambda: interrupt("transport_fault"),
        lambda: ack(at=1010, session_id=OTHER),
        lambda: ClockFact(at_ms=1200),
        lambda: interrupt("death_candidate"),
    ],
)
def test_missing_cleanup_stays_visible_and_success_never_follows(stop):
    m = machine()
    first = m.submit(stop())
    assert first.release_required and first.state != "ready"
    for f in (ack(at=1150), interval(at=1151), seal(at=1152), release(at=1153, frame=99)):
        d = m.submit(f)
        assert d.state == first.state and d.reason == first.reason and d.candidate is None
        assert d.release_required and not d.fresh


def test_late_release_after_every_terminal_kind_only_clears_cleanup():
    for stop in (
        lambda: interrupt("pause"),
        lambda: interrupt("death_candidate"),
        lambda: interrupt("disconnect"),
        lambda: ClockFact(at_ms=1200),
        lambda: change("room_change", room_visit=2),
    ):
        m = machine()
        first = m.submit(stop())
        d = m.submit(release(at=1300, frame=110))
        assert (d.state, d.reason) == (first.state, first.reason)
        assert d.release_required is False and d.candidate is None and not d.fresh


def test_release_at_deadline_is_applied_as_late_release_but_does_not_complete():
    m = machine()
    feed(m, ack(), interval(), seal())
    d = m.submit(release(at=1200))
    assert (d.state, d.reason, d.fresh) == ("expired", "wall_deadline", True)
    assert d.candidate is None and d.release_required is False


@pytest.mark.parametrize("last", range(4))
def test_deadline_wins_same_timestamp_tie_for_the_completing_fact(last):
    facts = [f(at=1100) for f in FULL]
    m = machine()
    feed(m, *facts[:last], *facts[last + 1 :])
    d = m.submit(dataclasses.replace(facts[last], at_ms=1200))
    assert (d.state, d.reason, d.candidate) == ("expired", "wall_deadline", None)
    assert d.state != "ready"


def test_completion_one_millisecond_before_deadline_is_accepted():
    d = feed(machine(), ack(), interval(), release(), seal(at=1199))
    assert d.state == "ready"


def test_expiry_before_at_and_after_endpoint():
    early = feed(machine(), ClockFact(at_ms=1005), ClockFact(at_ms=1200))
    mid = feed(machine(), ack(), interval(), ClockFact(at_ms=1300))
    after = machine()
    feed(after, *(f() for f in FULL))
    late = after.submit(ClockFact(at_ms=1300))
    assert (early.state, mid.state, late.state) == ("expired", "expired", "ready")


def test_authority_is_not_extendable_or_renewable():
    command = StepCommand(
        session_id=SESSION, sequence=1, game_epoch=1, room_visit=1, frame_id=100, frames=6
    )
    for deadline in (START, START - 1, START + 251):
        with pytest.raises(ProtocolError):
            NativeStepLifecycle(
                command, baseline_last_event_id=0, started_ms=START, deadline_ms=deadline
            )
    ok = NativeStepLifecycle(command, baseline_last_event_id=0, started_ms=START, deadline_ms=1250)
    assert ok.submit(ClockFact(at_ms=1249)).state == "waiting"
    gone = ok.submit(ClockFact(at_ms=1250))
    assert gone.state == "expired"
    assert ok.submit(ack(at=1251)).state == "expired"  # no renewal by later facts


def test_pause_transition_death_at_the_endpoint_fail_closed_before_ready():
    for kind in ("pause", "death_candidate"):
        m = machine()
        feed(m, ack(), interval(), release())
        d = m.submit(interrupt(kind, at=1035, frame=107))
        assert d.candidate is None and d.state != "waiting"
        assert not m.submit(seal(at=1040)).candidate
    m = machine()
    feed(m, ack(), interval(), release())
    assert m.submit(change("room_change", frame=107, room_visit=2)).state == "cancelled"


def test_conflicting_interrupt_after_ready_withholds_future_candidates():
    m = machine()
    ready = feed(m, *(f() for f in FULL))
    d = m.submit(interrupt("pause", at=1050, frame=107))
    assert (d.state, d.candidate, d.fresh) == ("ready", None, False)
    assert ready.candidate is not None  # Previously returned values remain immutable.
    assert d.conflict_after_ready is True
    m2 = machine()
    feed(m2, *(f() for f in FULL))
    assert m2.submit(interrupt("pause", at=1050, frame=108)).conflict_after_ready is True
    m3 = machine()
    feed(m3, *(f() for f in FULL))
    assert m3.submit(seal(at=1050, wm=10)).conflict_after_ready is True


def test_timestamp_regression_and_pre_start_facts_fault():
    m = machine()
    m.submit(ack(at=1010))
    assert m.submit(interval(at=1009)).reason == "timestamp_regression"
    assert machine().submit(ack(at=999)).reason == "timestamp_regression"


def test_non_fact_objects_fault_and_do_not_mutate():
    m = machine()
    for junk in (None, {"frame": 1}, "ack", 7):
        assert machine().submit(junk).reason == "malformed_fact"
    assert m.submit(object()).state == "faulted"


@pytest.mark.parametrize(
    "build",
    [
        lambda: ack(frame=True),
        lambda: ack(frame=-1),
        lambda: ack(frame=2**53),
        lambda: ack(frame=1.0),
        lambda: ack(at=True),
        lambda: ack(session_id="A" * 32),
        lambda: ack(session_id="a" * 31),
        lambda: ack(sequence="1"),
        lambda: interval(end=None),
        lambda: seal(wm=-1),
        lambda: ClockFact(at_ms=-1),
        lambda: interrupt("death"),
        lambda: change("floor"),
    ],
)
def test_malformed_facts_cannot_be_constructed(build):
    with pytest.raises(ProtocolError):
        build()


def test_constructor_validates_inputs():
    command = StepCommand(
        session_id=SESSION, sequence=1, game_epoch=1, room_visit=1, frame_id=100, frames=6
    )
    with pytest.raises(ProtocolError):
        NativeStepLifecycle(object(), baseline_last_event_id=0, started_ms=0, deadline_ms=10)
    for bad in (-1, True, 2**53, "1"):
        with pytest.raises(ProtocolError):
            NativeStepLifecycle(command, baseline_last_event_id=bad, started_ms=0, deadline_ms=10)


def test_fact_limit_64_ok_and_65_faults_without_eviction():
    m = machine()
    for i in range(MAX_FACTS):
        d = m.submit(ClockFact(at_ms=1001 + i))
        assert d.state == "waiting"
    assert d.facts_counted == 64
    over = m.submit(ClockFact(at_ms=1100))
    assert (over.state, over.reason) == ("faulted", "overflow")
    assert over.facts_counted == MAX_FACTS


def test_sixty_fourth_duplicate_still_counts_and_can_complete():
    m = machine()
    feed(m, ack(), interval(), release())
    for i in range(MAX_FACTS - 4):
        m.submit(ack(at=1031 + i))
    d = m.submit(seal(at=1100))
    assert d.state == "ready" and d.facts_counted == MAX_FACTS
    over = m.submit(ClockFact(at_ms=1101))
    assert over.state == "ready" and over.reason == "all_evidence_agrees"


def test_overflow_is_absorbing_and_cannot_be_resurrected():
    m = machine()
    for i in range(MAX_FACTS + 1):
        d = m.submit(ClockFact(at_ms=1001 + i))
    assert d.reason == "overflow"
    for f in (ack(at=1150), interval(at=1151), release(at=1152), seal(at=1153)):
        assert m.submit(f).state == "faulted"


def test_fault_is_absorbing_against_replay_and_late_completion():
    m = machine()
    feed(m, ack(), interval(), release())
    assert m.submit(interrupt("transport_fault")).state == "faulted"
    d = feed(m, seal(at=1100), seal(at=1101))
    assert (d.state, d.candidate, d.fresh) == ("faulted", None, False)
    replay = feed(m, *(f(at=1110 + i) for i, f in enumerate(FULL)))
    assert replay.state == "faulted" and replay.reason == "transport_fault"


def test_new_session_facts_cannot_revive_a_finished_step():
    m = machine()
    m.submit(interrupt("pause"))
    fresh = [
        ack(at=1100, session_id=OTHER, sequence=1),
        interval(at=1101, session_id=OTHER),
        seal(at=1102, session_id=OTHER),
        release(at=1103, session_id=OTHER),
    ]
    d = feed(m, *fresh)
    assert d.state == "cancelled" and d.release_required and d.candidate is None


def test_outputs_are_immutable_and_detached_from_inputs():
    m = machine()
    a = ack()
    d = feed(m, a, interval(), release(), seal())
    for target, field in ((d, "state"), (d.candidate, "end_frame"), (a, "frame_id")):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(target, field, 0)
    assert isinstance(d.missing, tuple)
    assert d.candidate == m.submit(ClockFact(at_ms=1100)).candidate


def test_decision_exposes_no_event_policy_or_serialization_surface():
    d = feed(machine(), *(f() for f in FULL))
    names = {f.name for f in dataclasses.fields(d)} | {
        f.name for f in dataclasses.fields(d.candidate)
    }
    assert not names & {"event", "events", "reward", "observation", "receipt", "completion"}
    assert not hasattr(d.candidate, "model_dump_json") and not hasattr(d, "wire_bytes")


def test_does_not_use_other_evidence_to_ready():
    # Repeated queries, snapshots and HP samples have no fact type: only the four count.
    m = machine()
    for i in range(30):
        m.submit(ClockFact(at_ms=1001 + i))
    d = m.submit(ack(at=1040))
    assert d.state == "waiting" and d.missing == ("interval", "release", "seal")


def test_early_release_is_not_cleanup_for_a_later_interruption():
    m = machine()
    feed(m, ack(), release(frame=101))
    stopped = m.submit(interrupt("pause", frame=104))
    assert stopped.release_required
    assert m.submit(release(at=1110, frame=103)).release_required
    assert not m.submit(release(at=1120, frame=104)).release_required


def test_late_release_cannot_precede_the_observed_stop_frame():
    m = machine()
    m.submit(interrupt("pause", frame=104))
    assert m.submit(release(at=1110, frame=100)).release_required


def test_terminal_clock_still_enforces_monotonic_cleanup_time():
    m = machine()
    m.submit(interrupt("pause"))
    m.submit(ClockFact(at_ms=1300))
    assert m.submit(release(at=1200, frame=104)).release_required


def test_overflow_cannot_make_valid_late_cleanup_impossible():
    m = machine()
    for _ in range(MAX_FACTS + 1):
        stopped = m.submit(ClockFact(at_ms=1100))
    assert stopped.reason == "overflow" and stopped.release_required
    clean = m.submit(release(at=1300, frame=104))
    assert clean.state == "faulted" and not clean.release_required
    assert clean.facts_counted == MAX_FACTS and clean.candidate is None


@pytest.mark.parametrize("kind", ["transport_fault", "disconnect", "authority_lost"])
def test_failure_after_endpoint_but_before_delivery_invalidates_ready(kind):
    m = machine()
    original = feed(m, *(f() for f in FULL))
    changed = m.submit(interrupt(kind, at=1050, frame=108))
    assert changed.conflict_after_ready and changed.candidate is None
    assert original.candidate is not None
    assert m.submit(ClockFact(at_ms=1060)).candidate is None


@pytest.mark.parametrize("bad", [None, ack(at=1039), release(at=1050, sequence=2)])
def test_malformed_regressing_or_foreign_fact_invalidates_ready(bad):
    m = machine()
    feed(m, *(f() for f in FULL))
    changed = m.submit(bad)
    assert changed.conflict_after_ready and changed.candidate is None


@pytest.mark.parametrize("kind", ["epoch_change", "session_change"])
def test_new_context_may_reset_its_frame_counter(kind):
    fact = (
        change(kind, game_epoch=2, frame=0)
        if kind == "epoch_change"
        else change(kind, session_id=OTHER, frame=0)
    )
    stopped = machine().submit(fact)
    expected = "unsupported_terminal" if kind == "epoch_change" else "faulted"
    assert stopped.state == expected and stopped.reason in {"epoch_change", "session_changed"}


def test_later_interruption_requires_new_cleanup_without_reviving_outcome():
    m = machine()
    stopped = m.submit(interrupt("pause", frame=104))
    assert not m.submit(release(at=1110, frame=104)).release_required
    changed = m.submit(interrupt("input_fault", at=1120, frame=105))
    assert changed.release_required and changed.state == stopped.state
    clean = m.submit(release(at=1130, frame=105))
    assert not clean.release_required and clean.candidate is None and not clean.fresh


def test_ready_candidate_is_withheld_after_evidence_budget_without_new_state():
    m = machine()
    original = feed(m, *(f() for f in FULL))
    for _ in range(MAX_FACTS):
        decision = m.submit(ClockFact(at_ms=1100))
    assert decision.state == original.state and not decision.fresh
    assert decision.conflict_after_ready and decision.candidate is None
    assert decision.facts_counted == MAX_FACTS


@pytest.mark.parametrize(
    "fact",
    [
        change("room_change", room_visit=2),
        change("floor_change"),
        change("epoch_change", game_epoch=2, frame=0),
        change("session_change", session_id=OTHER, frame=0),
    ],
)
def test_context_change_does_not_reuse_old_context_cleanup(fact):
    m = machine()
    feed(m, ack(), interval(), release())
    stopped = m.submit(fact)
    assert stopped.state != "ready" and stopped.release_required
    assert stopped.candidate is None


@pytest.mark.parametrize(
    "fact",
    [
        change("room_change", room_visit=2),
        change("floor_change"),
        change("epoch_change", game_epoch=2, frame=0),
        change("session_change", session_id=OTHER, frame=0),
    ],
)
def test_context_change_after_ready_also_invalidates_cleanup(fact):
    m = machine()
    original = feed(m, *(f() for f in FULL))
    stopped = m.submit(fact)
    assert stopped.state == original.state and stopped.conflict_after_ready
    assert stopped.release_required and stopped.candidate is None
