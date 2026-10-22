"""OFFLINE episode lifecycle tests on a toy simulator and scripted backends."""

import pytest
from synthetic import event, frame

from isaac_threrisaifuture.episodes import (
    ALL_TERMINAL_KINDS,
    Action,
    EpisodeController,
    EpisodeFault,
    Scenario,
    StepResult,
)
from isaac_threrisaifuture.sim import SyntheticRoomBackend

FULL = ALL_TERMINAL_KINDS
NONE: frozenset[str] = frozenset()
DIED_ONLY = frozenset({"player_died"})
CLEAR_ONLY = frozenset({"room_cleared"})


def scenario(**changes: object) -> Scenario:
    values: dict[str, object] = dict(
        id="toy",
        split="train",
        difficulty=1,
        max_game_updates=6,
        enemy_count=1,
        enemy_hp=7.0,
    )
    values.update(changes)
    return Scenario(**values)  # type: ignore[arg-type]


class Scripted:
    """Replays prepared StepResults; records release calls."""

    def __init__(self, results: list[StepResult]) -> None:
        self.results = list(results)
        self.released = 0

    def start_episode(self, scenario: Scenario, seed: int | None) -> StepResult:
        return self.results.pop(0)

    def step(self, action: Action, repeat: int) -> StepResult:
        return self.results.pop(0)

    def release(self) -> None:
        self.released += 1

    def close(self) -> None:
        pass


def play(coverages, kinds_at=None):
    """Run a scripted one-update-per-step episode to its end.

    coverages[i] is the coverage claim of result i (0 is the initial result);
    kinds_at maps a result index to the terminal event kinds it carries. The
    scenario limit is the last result's update count.
    """
    kinds_at = kinds_at or {}
    results = [
        StepResult(
            frame(frame_id=i + 1),
            tuple(event(kind, frame_id=i + 1) for kind in kinds_at.get(i, ())),
            coverage,
        )
        for i, coverage in enumerate(coverages)
    ]
    backend = Scripted(results)
    controller = EpisodeController(backend, repeat=1)
    controller.start(scenario(max_game_updates=len(coverages) - 1))
    last = None
    while controller.running:
        last = controller.step(Action())
    assert last is not None
    return last, controller, backend


def test_timeout_truncates_without_terminating():
    controller = EpisodeController(SyntheticRoomBackend(), repeat=3)
    controller.start(scenario())
    first = controller.step(Action())
    last = controller.step(Action())
    assert not first.truncated and last.truncated and not last.terminated
    assert last.outcome == "timeout" and last.summary.game_updates == 6


def test_clear_terminates_and_releases_control():
    backend = SyntheticRoomBackend()
    controller = EpisodeController(backend, repeat=1)
    controller.start(scenario(enemy_count=0))
    transition = controller.step(Action())
    assert transition.terminated and transition.outcome == "cleared"
    assert transition.summary.room_cleared and not transition.summary.died
    assert backend.release_calls >= 1 and not controller.running


def test_death_is_terminal_and_wins_a_same_interval_tie():
    first = frame(frame_id=1)
    both = StepResult(
        frame(frame_id=2),
        (event("room_cleared", frame_id=2), event("player_died", frame_id=2)),
    )
    controller = EpisodeController(Scripted([StepResult(first, ()), both]), repeat=1)
    controller.start(scenario())
    transition = controller.step(Action())
    assert transition.outcome == "death" and transition.summary.died
    # Facts record observed events; only the outcome applies death-over-clear precedence.
    assert transition.summary.room_cleared is True


def test_missing_coverage_defaults_to_unknown_and_never_becomes_a_timeout():
    assert StepResult(frame(), ()).terminal_coverage == frozenset()
    last, controller, backend = play([NONE, NONE, NONE])
    assert last.outcome == "unknown" and last.truncated and not last.terminated
    assert last.summary.outcome == "unknown" and last.summary.game_updates == 2
    assert last.summary.died is None and last.summary.room_cleared is None
    assert backend.released >= 1 and not controller.running


def test_complete_coverage_without_events_is_a_timeout():
    last, _, _ = play([FULL, FULL, FULL])
    assert last.outcome == "timeout" and last.truncated and not last.terminated
    assert last.summary.died is False and last.summary.room_cleared is False


@pytest.mark.parametrize(
    ("coverage", "died", "cleared"),
    [(DIED_ONLY, False, None), (CLEAR_ONLY, None, False)],
)
def test_partial_coverage_at_the_limit_is_unknown_with_per_kind_facts(coverage, died, cleared):
    last, _, _ = play([coverage] * 3)
    assert last.outcome == "unknown" and last.truncated and not last.terminated
    assert (last.summary.died, last.summary.room_cleared) == (died, cleared)


@pytest.mark.parametrize(
    ("coverages", "died", "cleared"),
    [
        ([FULL, FULL, NONE], None, None),  # coverage lost in the last interval
        ([FULL, NONE, FULL, FULL], None, None),  # a later complete interval does not repair it
        ([NONE, FULL, FULL], None, None),  # a gap in the initial result persists
        ([FULL, DIED_ONLY, FULL, FULL], False, None),  # only the lost kind becomes unknown
    ],
)
def test_a_coverage_gap_in_any_interval_makes_the_kind_unknown(coverages, died, cleared):
    last, _, _ = play(coverages)
    assert last.outcome == "unknown" and last.truncated and not last.terminated
    assert (last.summary.died, last.summary.room_cleared) == (died, cleared)


def test_coverage_is_tracked_per_kind_before_the_episode_ends():
    backend = Scripted(
        [StepResult(frame(frame_id=1), (), DIED_ONLY), StepResult(frame(frame_id=2), (), DIED_ONLY)]
    )
    controller = EpisodeController(backend, repeat=1)
    started = controller.start(scenario(max_game_updates=9))
    assert started.summary.died is False and started.summary.room_cleared is None
    running = controller.step(Action())
    assert running.outcome is None and not running.terminated and not running.truncated
    assert running.summary.died is False and running.summary.room_cleared is None
    assert controller.running


def test_a_new_episode_does_not_inherit_the_previous_coverage_gap():
    results = [
        StepResult(frame(frame_id=1), (), NONE),
        StepResult(frame(frame_id=2), (), NONE),
        StepResult(frame(frame_id=3), (), FULL),
        StepResult(frame(frame_id=4), (), FULL),
    ]
    controller = EpisodeController(Scripted(results), repeat=1)
    controller.start(scenario(max_game_updates=1))
    assert controller.step(Action()).outcome == "unknown"
    controller.start(scenario(max_game_updates=1))
    assert controller.step(Action()).outcome == "timeout"


@pytest.mark.parametrize("coverage", [FULL, NONE])
@pytest.mark.parametrize(
    "kinds", [("player_died",), ("room_cleared",), ("player_died", "room_cleared")]
)
def test_terminal_initial_result_faults_and_never_allows_an_action(coverage, kinds):
    initial = StepResult(
        frame(frame_id=1), tuple(event(kind, frame_id=1) for kind in kinds), coverage
    )
    pending = StepResult(frame(frame_id=2), (), coverage)
    backend = Scripted([initial, pending])
    controller = EpisodeController(backend, repeat=1)
    with pytest.raises(EpisodeFault, match="initial.*terminal"):
        controller.start(scenario())
    assert not controller.running and backend.released == 1
    assert len(controller.faults) == 1
    assert backend.results == [pending]
    with pytest.raises(RuntimeError, match="No running episode"):
        controller.step(Action())
    assert backend.results == [pending]


def test_known_death_needs_no_coverage():
    last, controller, backend = play([NONE, NONE, NONE], {1: ("player_died",)})
    assert last.outcome == "death" and last.terminated and not last.truncated
    assert last.summary.died is True and last.summary.room_cleared is None
    assert backend.released >= 1 and not controller.running


def test_known_clear_with_complete_coverage():
    last, controller, backend = play([FULL, FULL, FULL], {1: ("room_cleared",)})
    assert last.outcome == "cleared" and last.terminated and not last.truncated
    assert last.summary.room_cleared is True and last.summary.died is False
    assert backend.released >= 1 and not controller.running


@pytest.mark.parametrize(
    "coverages",
    [
        [CLEAR_ONLY] * 4,  # death never covered
        [FULL, NONE, FULL, FULL],  # death coverage lost earlier; the clear interval is complete
    ],
)
def test_clear_with_incomplete_death_coverage_is_unknown_and_releases(coverages):
    last, controller, backend = play(coverages, {2: ("room_cleared",)})
    assert last.outcome == "unknown" and last.truncated and not last.terminated
    assert last.summary.game_updates == 2 and not controller.running
    assert last.summary.room_cleared is True and last.summary.died is None
    assert backend.released >= 1
    with pytest.raises(RuntimeError):
        controller.step(Action())


@pytest.mark.parametrize("bad", [frozenset({"enemy_killed"}), "player_died", {"player_died"}])
def test_invalid_coverage_claims_are_rejected(bad):
    with pytest.raises(ValueError):
        StepResult(frame(), (), bad)


def test_synthetic_backend_explicitly_declares_complete_coverage():
    backend = SyntheticRoomBackend()
    assert backend.start_episode(scenario(), 1).terminal_coverage == FULL
    assert backend.step(Action(), 1).terminal_coverage == FULL


def test_transport_fault_is_not_a_game_outcome():
    backend = SyntheticRoomBackend(fail_after_updates=2)
    controller = EpisodeController(backend, repeat=3)
    controller.start(scenario(max_game_updates=60))
    with pytest.raises(EpisodeFault):
        controller.step(Action())
    assert controller.faults[0].episode_id == 1
    assert backend.release_calls >= 1 and not controller.running
    with pytest.raises(RuntimeError):
        controller.step(Action())


def test_next_episode_after_fault_gets_a_new_identity():
    controller = EpisodeController(SyntheticRoomBackend(fail_after_updates=1), repeat=3)
    controller.start(scenario(max_game_updates=60))
    with pytest.raises(EpisodeFault):
        controller.step(Action())
    controller.start(scenario())  # the backend is still failing, so this episode faults too
    with pytest.raises(EpisodeFault):
        controller.step(Action())
    assert [f.episode_id for f in controller.faults] == [1, 2]


@pytest.mark.parametrize(
    "bad",
    [
        StepResult(frame(frame_id=1), ()),  # repeated frame
        StepResult(frame(frame_id=2, game_epoch=2), ()),  # new epoch
        StepResult(frame(frame_id=2, room_visit=2), ()),  # room change
        StepResult(frame(frame_id=2, session_id="b" * 32), ()),  # other session
        StepResult(frame(frame_id=2), (event(frame_id=1),)),  # event outside the interval
    ],
)
def test_identity_violations_are_faults(bad):
    backend = Scripted([StepResult(frame(frame_id=1), ()), bad])
    controller = EpisodeController(backend, repeat=1)
    controller.start(scenario())
    with pytest.raises(EpisodeFault):
        controller.step(Action())
    assert backend.released >= 1 and len(controller.faults) == 1


def test_room_change_is_allowed_when_the_scenario_says_so():
    backend = Scripted(
        [StepResult(frame(frame_id=1), ()), StepResult(frame(frame_id=2, room_visit=2), ())]
    )
    controller = EpisodeController(backend, repeat=1)
    controller.start(scenario(allow_room_change=True))
    assert controller.step(Action()).outcome is None


def test_stop_releases_and_is_idempotent():
    backend = SyntheticRoomBackend()
    controller = EpisodeController(backend)
    controller.start(scenario())
    controller.stop()
    controller.stop()
    assert backend.release_calls == 2 and not controller.running


def test_one_hundred_consecutive_short_episodes_need_no_manual_recovery():
    controller = EpisodeController(SyntheticRoomBackend(), repeat=3)
    for expected in range(1, 101):
        controller.start(scenario(), seed=expected)
        transition = None
        while controller.running:
            transition = controller.step(Action())
        assert transition is not None and transition.episode_id == expected
        assert transition.outcome == "timeout"
        assert transition.summary.died is False and transition.summary.room_cleared is False
    assert controller.faults == []


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        Action(move=5)
    for use in (-1, 4):
        with pytest.raises(ValueError):
            Action(use=use)
    with pytest.raises(ValueError):
        EpisodeController(SyntheticRoomBackend(), repeat=0)
    with pytest.raises(ValueError):
        scenario(max_game_updates=0)
