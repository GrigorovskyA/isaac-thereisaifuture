"""The recording CLI is finite and never requests actions or restarts."""

import pytest
from test_entity_transport import entity_snapshot, record
from test_observer import ack

from isaac_threrisaifuture import entity_probe
from isaac_threrisaifuture.entities import EntitySnapshot
from isaac_threrisaifuture.observation import BridgeTimeout, HelloAck, decode
from isaac_threrisaifuture.recording import open_replay


class SimulatedClient:
    instances = []
    fault = False

    def __init__(self, config):
        self.config = config
        self.address = ("127.0.0.1", 0)
        self.received = 0
        self.closed = False
        self.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def accept(self):
        return decode(record(ack("a" * 32)).rstrip(b"\n"), HelloAck)

    def receive(self):
        self.received += 1
        if self.fault:
            raise BridgeTimeout("Injected simulated peer failure")
        return decode(
            record(entity_snapshot("a" * 32, self.received)).rstrip(b"\n"), EntitySnapshot
        )


def test_probe_obeys_sample_budget_and_keeps_modes_read_only(tmp_path, monkeypatch):
    monkeypatch.setattr(entity_probe, "ObservationClient", SimulatedClient)
    path = tmp_path / "frames.jsonl"
    assert entity_probe.main(["--output", str(path), "--samples", "3"]) == 0
    client = SimulatedClient.instances[-1]
    assert client.received == 3 and client.closed
    assert client.config.entity_observations
    assert not client.config.safe_actions and not client.config.restart_after_death
    _, records = open_replay(path, "policy_frames")
    assert len(list(records)) == 3
    assert entity_probe.main(["--output", str(path)]) == 2  # Never overwrite evidence.


def test_probe_fault_closes_sockets_and_leaves_only_completed_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(entity_probe, "ObservationClient", SimulatedClient)
    monkeypatch.setattr(SimulatedClient, "fault", True)
    path = tmp_path / "partial.jsonl"
    assert entity_probe.main(["--output", str(path)]) == 2
    assert SimulatedClient.instances[-1].closed
    assert len(path.read_text().splitlines()) == 1  # Manifest only; not successful data.


@pytest.mark.parametrize(
    "budget", [["--samples", "501"], ["--samples", "0"], ["--seconds", "nan"], ["--seconds", "301"]]
)
def test_probe_rejects_unbounded_or_invalid_budgets(tmp_path, budget):
    path = tmp_path / "absent.jsonl"
    with pytest.raises(SystemExit):
        entity_probe.main(["--output", str(path), *budget])
    assert not path.exists()
