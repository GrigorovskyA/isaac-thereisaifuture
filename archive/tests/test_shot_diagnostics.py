"""Directional proxies are not native tear hits or a controller."""

import pytest
from test_coherent_geometry import geometry_snapshot

from isaac_threrisaifuture.entities import EntityFrame
from isaac_threrisaifuture.shot_diagnostics import shot_evidence


def scene(x=120.0, y=0.0, line=True):
    snap = geometry_snapshot(clear=line)
    raw = snap.entity_frame.model_dump(mode="json")
    raw["entities"][0]["position"] = {"x": x, "y": y}
    return EntityFrame.model_validate(raw), snap.combat_geometry


@pytest.mark.parametrize("x,y,direction", [(-120, 0, 1), (120, 0, 2), (0, -120, 3), (0, 120, 4)])
def test_each_direction_distinguishes_clear_blocked_and_wrong_shot(x, y, direction):
    f, g = scene(x, y)
    e = shot_evidence(f, g)
    assert e.clear_directions == (direction,)
    assert e.classify(direction) == "selected_clear_proxy"
    assert e.classify(0) == "missed_clear_opportunity"
    assert e.classify(1 if direction != 1 else 2) == "wrong_direction_with_clear_opportunity"
    f, g = scene(x, y, False)
    assert shot_evidence(f, g).classify(direction) == "only_blocked_selected_direction"


def test_diagonal_cone_is_not_cardinal_alignment_and_range_is_separate():
    f, g = scene(120, 100)
    assert not shot_evidence(f, g).clear_directions
    assert shot_evidence(f, g).classify(2) == "no_aligned_target"
    f, g = scene(300, 0)
    assert shot_evidence(f, g).classify(2) == "aligned_out_of_range"


def test_unknown_line_and_missing_geometry_never_claim_blocked():
    f, g = scene(line=None)
    assert shot_evidence(f, g).classify(2) == "unknown_selected_line"
    assert shot_evidence(f, None).classify(2) == "unknown_weapon"
    g = g.model_copy(update={"weapon": "unsupported", "tear_range": None})
    assert shot_evidence(f, g).classify(2) == "unknown_weapon"


def test_overflow_prevents_negative_certainty_but_keeps_visible_clear_proxy():
    f, g = scene(line=False)
    f = f.model_copy(update={"source_overflow": {"enemy": 2}})
    assert shot_evidence(f, g).classify(2) == "incomplete_visible_set"
    assert shot_evidence(f, g).complete_visible_set is False
    g = g.model_copy(update={"enemies": [g.enemies[0].model_copy(update={"clear": True})]})
    assert shot_evidence(f, g).classify(2) == "selected_clear_proxy"


@pytest.mark.parametrize("change", [{"frame_id": 999}, {"enemies": []}])
def test_identity_and_missing_line_handling(change):
    f, g = scene()
    g = g.model_copy(update=change)
    if "frame_id" in change:
        with pytest.raises(ValueError, match="identity"):
            shot_evidence(f, g)
    else:
        assert shot_evidence(f, g).classify(2) == "unknown_selected_line"


@pytest.mark.parametrize("shoot", [True, -1, 5, 1.5])
def test_invalid_action(shoot):
    f, g = scene()
    with pytest.raises(ValueError):
        shot_evidence(f, g).classify(shoot)


@pytest.mark.parametrize("tolerance", [-1, 21, float("nan"), float("inf")])
def test_invalid_tolerance(tolerance):
    f, g = scene()
    with pytest.raises(ValueError):
        shot_evidence(f, g, axis_tolerance=tolerance)


def test_empty_scene_unknown_membership_and_explicit_sensitivity():
    f, g = scene(10, -210, False)
    assert shot_evidence(f, g).classify(3) == "no_aligned_target"
    assert shot_evidence(f, g, axis_tolerance=20).classify(3) == "only_blocked_selected_direction"
    f = f.model_copy(update={"entities": []})
    g = g.model_copy(update={"enemies": []})
    assert shot_evidence(f, g).classify(2) == "no_visible_enemy"


def test_raw_snapshot_is_not_an_input_and_diagnostics_do_not_mutate_it():
    snap = geometry_snapshot()
    saved = snap.model_dump(mode="json")
    shot_evidence(snap.entity_frame, snap.combat_geometry)
    assert snap.model_dump(mode="json") == saved
    with pytest.raises(TypeError):
        shot_evidence(snap, snap.combat_geometry)


def test_diagnostics_respect_encoder_enemy_capacity():
    f, g = scene()
    original = f.entities[0]
    enemies = [
        original.model_copy(
            update={
                "entity_id": i,
                "position": original.position.model_copy(update={"x": 100.0 + i}),
            }
        )
        for i in range(1, 18)
    ]
    f = f.model_copy(update={"entities": enemies})
    g = g.model_copy(update={"enemies": [g.enemies[0].model_copy(update={"entity_id": 17})]})
    evidence = shot_evidence(f, g)
    assert evidence.visible_enemies == 16
    assert evidence.complete_visible_set is False
    assert not evidence.clear_directions
