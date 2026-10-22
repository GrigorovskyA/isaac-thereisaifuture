"""Synthetic boundary evidence is not a native clearance or learning result."""

from dataclasses import replace

import numpy as np
import pytest
from test_firing_position import sample

from isaac_threrisaifuture import firing_progress_v4 as v4
from isaac_threrisaifuture import firing_progress_v5 as v5
from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.entities import Vec
from isaac_threrisaifuture.live import LiveRunOptions, LiveSnapshot
from isaac_threrisaifuture.observer_client import ObserverConfig


def corner(frame=1, x=30.0, y=130.0, *, clear=True, support=True, target=1, visit=1):
    mask = "".join("1" if 1 <= x <= 5 and 1 <= y <= 3 else "0" for y in range(5) for x in range(7))
    raw = sample(
        frame, x=x, target=target, visit=visit, grid_changes={"walkable": mask}
    ).model_dump(mode="json")
    pos = {"x": x, "y": y}
    raw["player"]["position"] = pos
    raw["entity_frame"]["player_position"] = pos
    raw["entity_frame"]["entities"][0]["position"] = {"x": 280 - x, "y": 80 - y}
    snap = LiveSnapshot.model_validate(raw)
    if support:
        index, q = v5.nearest_patch(snap.oracle.navigation.grid, Vec(**pos))
        raw["oracle"]["firing"]["boundary_support"] = {
            "version": 1,
            "patch": index,
            "source": pos,
            "position": q.model_dump(),
            "clear": clear,
        }
    return LiveSnapshot.model_validate(raw)


def value(snap, fn=v5.potential):
    return fn(snap.oracle.navigation.grid, snap.oracle.firing, snap.entity_frame.player_position)


@pytest.mark.parametrize("x,y", [(35, 130), (30, 125), (40, 130), (30, 120), (40, 120)])
def test_first_escape_has_signed_signal_and_retreat_does_not_pay(x, y):
    a, b = corner(), corner(4, x, y)
    assert value(a, v4.potential) is None
    assert value(b) > value(a)
    forward = v5.FiringProgressV5()
    forward.begin(a)
    assert forward.transition(a, b) > 0
    back = v5.FiringProgressV5()
    back.begin(corner(x=x, y=y))
    assert back.transition(corner(x=x, y=y), corner(4)) < 0


def test_corner_to_interior_is_continuous_and_open_row_sign_is_unchanged():
    assert value(corner(x=40, y=120.000001)) == pytest.approx(value(corner(x=40, y=120)), abs=1e-8)
    scores = [value(sample(x=float(x))) for x in range(1, 161)]
    assert all(a < b for a, b in zip(scores, scores[1:], strict=False))
    for x in range(1, 161):
        assert value(sample(x=float(x))) == value(sample(x=float(x)), v4.potential)


@pytest.mark.parametrize("clear,support", [(False, True), (None, True), (True, False)])
def test_unmeasured_or_blocked_link_is_unknown_and_never_pays(clear, support):
    assert value(corner(clear=clear, support=support)) is None
    ledger = v5.FiringProgressV5()
    a, b = corner(), corner(4, 35, 130, clear=clear, support=support)
    ledger.begin(a)
    assert ledger.transition(a, b) == 0


@pytest.mark.parametrize(
    "field,new", [("source", {"x": 31, "y": 130}), ("position", {"x": 80, "y": 120}), ("patch", 9)]
)
def test_pose_projection_and_patch_mismatch_are_not_trusted(field, new):
    raw = corner().model_dump(mode="json")
    raw["oracle"]["firing"]["boundary_support"][field] = new
    assert value(LiveSnapshot.model_validate(raw)) is None


def test_blocked_or_unreachable_patch_and_long_links_are_unknown():
    raw = corner().model_dump(mode="json")
    raw["oracle"]["navigation"]["grid"]["walkable"] = "0" * 35
    assert value(LiveSnapshot.model_validate(raw)) is None
    raw = corner().model_dump(mode="json")
    raw["oracle"]["firing"]["clear_cells"] = []
    assert value(LiveSnapshot.model_validate(raw)) is None
    assert v5.nearest_patch(corner().oracle.navigation.grid, Vec(x=-100, y=130)) is None


def test_stationary_oscillation_reset_reentry_and_targets_share_cap():
    ledger = v5.FiringProgressV5()
    ledger.begin(corner())
    assert ledger.transition(corner(), corner(4)) == 0
    paid = ledger.transition(corner(4), corner(7, 35, 125))
    assert paid > 0
    retreat = ledger.transition(corner(7, 35, 125), corner(10))
    recovery = ledger.transition(corner(10), corner(13, 35, 125))
    assert retreat < 0 < recovery
    assert retreat + recovery == pytest.approx(0)
    ledger.begin(corner(16, visit=2))
    assert ledger.transition(corner(16, visit=2), corner(19, 35, 125, visit=2)) == 0
    for t in range(2, 80):
        a = corner(t * 10, target=t)
        b = corner(t * 10 + 3, 40, 120, target=t)
        ledger.begin(a)
        paid += ledger.transition(a, b)
    assert 0 < paid <= 0.25


def test_recovery_below_previous_record_refunds_only_charged_debt_across_reset_reentry():
    ledger = v5.FiringProgressV5()
    best = corner(x=40, y=120)
    ledger.begin(best)
    retreat = ledger.transition(best, corner(4))
    assert retreat < 0
    ledger.begin(corner(7, visit=2))
    refund = ledger.transition(corner(7, visit=2), corner(10, 35, 125, visit=2))
    assert refund > 0
    assert refund <= -retreat
    for i in range(10):
        a, b, c = corner(20 + i * 9, 35, 125), corner(23 + i * 9), corner(26 + i * 9, 35, 125)
        ledger.begin(a)
        assert ledger.transition(a, b) + ledger.transition(b, c) == pytest.approx(0)


def test_stationary_and_unknown_geometry_never_create_recovery_debt():
    ledger = v5.FiringProgressV5()
    a, b, c = corner(), corner(4), corner(7, clear=None)
    ledger.begin(a)
    assert ledger.transition(a, b) == 0
    assert ledger.transition(b, c) == 0
    assert not ledger._debt


def test_unknown_current_goal_field_cannot_refund_old_retreat_debt():
    ledger = v5.FiringProgressV5()
    best, away = corner(x=40, y=120), corner(4)
    ledger.begin(best)
    assert ledger.transition(best, away) < 0
    debt = dict(ledger._debt)
    raw = corner(7, 35, 125).model_dump(mode="json")
    raw["oracle"]["firing"]["target_position"]["x"] = 420.0
    raw["entity_frame"]["entities"][0]["position"]["x"] = 420.0 - 35.0
    after = LiveSnapshot.model_validate(raw)
    assert value(after) is None
    assert ledger.transition(away, after) == 0
    assert ledger._debt == debt


def test_room_debt_is_bounded_across_targets_and_refunds_never_exceed_charges():
    ledger = v5.FiringProgressV5()
    signed = 0.0
    for target in range(1, 81):
        a = corner(target * 10, 40, 120, target=target)
        b = corner(target * 10 + 3, target=target)
        ledger.begin(a)
        signed += ledger.transition(a, b)
    assert signed == pytest.approx(-0.25)
    assert sum(ledger._room_debt.values()) == pytest.approx(0.25)
    assert sum(ledger._debt.values()) == pytest.approx(0.25)
    for target in range(1, 81):
        a = corner(1000 + target * 10, target=target)
        b = corner(1003 + target * 10, 40, 120, target=target)
        ledger.begin(a)
        signed += ledger.transition(a, b)
    assert signed == pytest.approx(0)
    assert sum(ledger._room_debt.values()) == pytest.approx(0)


def test_patch_switch_rebases_unpaid():
    a, b = corner(), corner(4, 30, 70)
    assert a.oracle.firing.boundary_support.patch != b.oracle.firing.boundary_support.patch
    ledger = v5.FiringProgressV5()
    ledger.begin(a)
    assert ledger.transition(a, b) == 0


def test_reward_support_cannot_change_policy_inputs_or_legacy_value():
    a, b = corner(), corner(clear=False)
    np.testing.assert_array_equal(encode(a.entity_frame).vector, encode(b.entity_frame).vector)
    assert value(a, v4.potential) == value(b, v4.potential)


def test_option_dependencies():
    with pytest.raises(ValueError, match="Boundary"):
        LiveRunOptions("train", __import__("pathlib").Path("unused"), boundary_progress_reward=True)
    with pytest.raises(ValueError, match="Boundary"):
        replace(ObserverConfig(), boundary_support=True)
