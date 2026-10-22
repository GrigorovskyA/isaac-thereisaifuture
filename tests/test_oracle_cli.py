"""CLI bounds and cleanup with a fake transport."""

import json
import sys

import pytest

from isaac_threrisaifuture import cli
from isaac_threrisaifuture.observation import ProtocolError


class Record:
    def model_dump_json(self):
        return json.dumps({"test": "fake_readonly_record"})


@pytest.fixture
def transport(monkeypatch):
    class Client:
        made = []

        def __init__(self, config):
            self.config = config
            self.receives = 0
            self.closed = False
            self.address = ("127.0.0.1", 9528)
            self.made.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

        def accept(self):
            return Record()

        def receive(self):
            self.receives += 1
            return Record()

    monkeypatch.setattr(cli, "ObservationClient", Client)
    return Client


def run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["isaac-future", "observe", *args])
    cli.main()


def test_restart_mode_requires_confirmed_slot_before_opening_socket(transport, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        run(monkeypatch, "--restart-after-death")
    assert exc.value.code == 2 and not transport.made


def test_capability_rejection_closes_without_reconnect(transport, monkeypatch):
    def reject(self):
        raise ProtocolError("Missing diagnostic capability")

    monkeypatch.setattr(transport, "accept", reject)
    with pytest.raises(SystemExit) as exc:
        run(monkeypatch)
    assert exc.value.code == 2
    assert len(transport.made) == 1 and transport.made[0].closed


def test_keyboard_interrupt_closes_peer(transport, monkeypatch):
    def interrupt(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(transport, "receive", interrupt)
    run(monkeypatch)
    assert transport.made[0].closed


def test_default_cli_reads_the_requested_sample_count(transport, monkeypatch):
    run(monkeypatch, "--samples", "601")
    assert transport.made[0].receives == 601 and transport.made[0].closed
