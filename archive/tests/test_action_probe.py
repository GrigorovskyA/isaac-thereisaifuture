"""OFFLINE checks of the finite probe boundary; no Isaac interaction."""

import io
import time

import pytest
from test_actions import approval

from isaac_threrisaifuture.action_probe import run_probe, sequence_plan


@pytest.mark.parametrize("count", [0, 51, -1, True])
def test_invalid_budget_rejected_before_connecting(count):
    with pytest.raises(ValueError):
        run_probe(approval(), count, io.StringIO())


def test_expired_authority_rejected_before_connecting():
    with pytest.raises(ValueError, match="expired"):
        run_probe(approval(expires_at=int(time.time()) - 1), 1, io.StringIO())


def test_plan_covers_independent_axes_and_combined_cases():
    plan = sequence_plan(50)
    assert len(plan) == 50
    assert all(plan.count(case) == 5 for case in set(plan))
    assert {m for m, s in plan if s == "none"} == {"left", "right", "up", "down"}
    assert {s for m, s in plan if m == "none"} == {"left", "right", "up", "down"}
    assert ("right", "up") in plan and ("left", "down") in plan


def test_shooting_refreshes_do_not_repeat_movement(monkeypatch):
    from test_observer import ack, snapshot

    from isaac_threrisaifuture import action_probe
    from isaac_threrisaifuture.actions import CommandAck
    from isaac_threrisaifuture.observation import HelloAck, Snapshot

    class Peer:
        def __init__(self):
            self.commands = []
            self.sequence = 0
            self.closed = False

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

        def accept(self):
            return HelloAck.model_validate(ack("a" * 32))

        def receive(self):
            self.sequence += 1
            state = snapshot("a" * 32, self.sequence)
            state["player"]["position"] = {"x": 320.0, "y": 280.0}
            return Snapshot.model_validate(state)

        def command(self, kind, **kwargs):
            self.commands.append((kind, kwargs))
            return CommandAck(
                type="command_ack",
                protocol_version=1,
                session_id="a" * 32,
                sequence=len(self.commands),
                game_epoch=1,
                room_visit=1,
                frame_id=10,
                kind=kind,
                status="accepted",
            )

    peer = Peer()
    monkeypatch.setattr(action_probe, "ActionClient", lambda *args: peer)
    output = io.StringIO()
    action_probe.run_probe(approval(), 10, output)
    motion = [
        payload
        for kind, payload in peer.commands
        if kind == "action" and payload.get("move", "none") != "none"
    ]
    assert len(motion) == 6  # four movement-only cases plus two combined cases
    assert all(payload["frames"] == 2 for payload in motion)
    assert peer.closed
    assert "pending_evidence_review" in output.getvalue()
