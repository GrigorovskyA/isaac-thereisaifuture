"""OFFLINE tests for the read-only training dashboard."""

import csv
import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from isaac_threrisaifuture import dashboard
from isaac_threrisaifuture.checkpoints import save_checkpoint
from isaac_threrisaifuture.episode_metrics import FIELDS
from isaac_threrisaifuture.training_metrics import TRAIN_FIELDS


def line(i: int, **over: Any) -> str:
    row: dict[str, Any] = dict.fromkeys(FIELDS, "")
    row.update(
        episode_id=f"ep-{i}", scenario_id="s", timesteps=100 + i, outcome="terminated",
        end_reason="death", damage_dealt_fraction=0.5, rooms_cleared=i, max_stage=1,
        wall_time="2026-10-22T10:00:00+00:00",
    )  # fmt: skip
    row["return"] = i / 2
    row.update(over)
    return ",".join(str(row[name]) for name in FIELDS) + "\n"


def write_csv(root: Path, count: int, tail: str = "") -> Path:
    path = root / "metrics" / "episodes.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ",".join(FIELDS) + "\n" + "".join(line(i) for i in range(count)) + tail, "utf-8"
    )
    return path


def train_line(i: int, **over: Any) -> str:
    row: dict[str, Any] = dict.fromkeys(TRAIN_FIELDS, 0.0)
    row.update(wall_time="2026-10-22T10:00:00+00:00", timesteps=2048 * (i + 1), rollout_index=i + 1)
    row.update(move_none=1.0, shoot_none=1.0, use_none=1.0, explained_variance=0.5)
    row.update(over)
    return ",".join(str(row[name]) for name in TRAIN_FIELDS) + "\n"


def write_train(root: Path, count: int, tail: str = "") -> Path:
    path = root / "metrics" / "train.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ",".join(TRAIN_FIELDS) + "\n" + "".join(train_line(i) for i in range(count)) + tail,
        "utf-8",
    )
    return path


@pytest.fixture
def served(tmp_path: Path) -> Iterator[tuple[dashboard.DashboardServer, str]]:
    server = dashboard.DashboardServer(tmp_path, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def get(base: str, path: str) -> dict[str, Any]:
    with urllib.request.urlopen(base + path, timeout=5) as response:
        return json.loads(response.read())


class Artifact:
    def save(self, path: str) -> None:
        Path(path).write_bytes(b"x")


def test_missing_files_give_empty_state(served):
    server, base = served
    state = get(base, "/api/state?since=0")
    assert state["episodes"] == [] and state["total_episodes"] == 0
    assert state["latest_checkpoint"] is None and state["supervisor"] is None
    assert "server_time" in state


def test_rows_are_parsed_and_paged_with_since(served):
    server, base = served
    write_csv(server.state.run_root, 5)
    state = get(base, "/api/state")
    assert state["total_episodes"] == 5 and [r["index"] for r in state["episodes"]] == [
        0,
        1,
        2,
        3,
        4,
    ]
    row = state["episodes"][2]
    assert row["timesteps"] == 102 and row["return"] == 1.0 and row["outcome"] == "terminated"
    assert row["truncation_reason"] is None and row["wall_time"].startswith("2026-10-22")
    later = get(base, "/api/state?since=3")
    assert [r["index"] for r in later["episodes"]] == [3, 4] and later["total_episodes"] == 5
    assert get(base, "/api/state?since=99")["episodes"] == []
    assert get(base, "/api/state?since=junk")["total_episodes"] == 5


def test_partial_last_line_is_skipped_then_picked_up(served):
    server, base = served
    path = write_csv(server.state.run_root, 2, tail=line(2)[:25])
    assert get(base, "/api/state")["total_episodes"] == 2
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line(2)[25:])
    state = get(base, "/api/state?since=2")
    assert state["total_episodes"] == 3 and state["episodes"][0]["index"] == 2


def test_malformed_complete_rows_are_skipped(served):
    server, base = served
    write_csv(server.state.run_root, 1, tail="a,b\n" + line(7, timesteps="abc") + line(8))
    state = get(base, "/api/state")
    assert state["total_episodes"] == 2 and state["episodes"][1]["episode_id"] == "ep-8"


def test_truncation_and_recreation_restart_from_zero(served):
    server, base = served
    path = write_csv(server.state.run_root, 6)
    assert get(base, "/api/state")["total_episodes"] == 6
    write_csv(server.state.run_root, 2)  # shorter file
    assert get(base, "/api/state?since=6")["total_episodes"] == 2
    path.unlink()
    assert get(base, "/api/state")["total_episodes"] == 0
    write_csv(server.state.run_root, 3)
    assert [r["index"] for r in get(base, "/api/state")["episodes"]] == [0, 1, 2]


def test_response_row_cap(served, monkeypatch):
    server, base = served
    write_csv(server.state.run_root, 12)
    monkeypatch.setattr(dashboard, "MAX_ROWS", 5)
    first = get(base, "/api/state?since=0")
    assert len(first["episodes"]) == 5 and first["total_episodes"] == 12
    last = get(base, "/api/state?since=10")
    assert [r["index"] for r in last["episodes"]] == [10, 11]


def test_latest_checkpoint_is_read_from_a_real_save(served):
    server, base = served
    root = server.state.run_root / "seed-3" / "checkpoints"
    manifest = save_checkpoint(
        root, model=Artifact(), vec_normalize=Artifact(), algorithm="RecurrentPPO",
        cfg_hash="a" * 64, seed=3, timesteps=4096, parent_checkpoint_id=None, rng_state={},
        reward_contract="pure-v6", hyperparameters={"learning_rate": 0.001},
    )  # fmt: skip
    ckpt = get(base, "/api/state")["latest_checkpoint"]
    assert ckpt["checkpoint_id"] == manifest.checkpoint_id and ckpt["timesteps"] == 4096
    assert ckpt["rollout_index"] == 1 and ckpt["hyperparameters"] == {"learning_rate": 0.001}
    assert ckpt["seed"] == 3 and ckpt["created_at"].endswith("+00:00")


def test_supervisor_live_status_then_final_forever_json(served):
    server, base = served
    folder = server.state.run_root / "supervisor"
    for name, state in (("session-a-0001", "waiting"), ("session-b-0002", "training")):
        (folder / name).mkdir(parents=True)
        (folder / name / "status.json").write_text(
            json.dumps({"state": state, "updated_at": 1.7e9})
        )
    live = get(base, "/api/state")["supervisor"]
    assert live["state"] == "training" and live["session"] == "session-b-0002"
    assert live["finished"] is False and live["stop_reason"] is None
    assert live["updated_at"].startswith("2023-")
    (folder / "forever.json").write_text(json.dumps({"stop_reason": "stop file", "sessions": []}))
    done = get(base, "/api/state")["supervisor"]
    assert done["finished"] is True and done["stop_reason"] == "stop file"
    (folder / "session-b-0002" / "status.json").write_text("{not json")
    assert get(base, "/api/state")["supervisor"]["stop_reason"] == "stop file"


def test_html_page_and_unknown_routes(served):
    server, base = served
    with urllib.request.urlopen(base + "/") as response:
        body = response.read().decode()
        assert response.headers["Content-Type"].startswith("text/html")
    assert "/api/state" in body and "<svg" not in body.split("<script>")[0]
    for path in (
        "/x",
        "/api",
        "/api/state/",
        "/../etc/passwd",
        "/metrics/episodes.csv",
        "/supervisor/",
    ):
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(base + path)
        assert error.value.code == 404


def test_foreign_host_header_is_refused(served):
    server, base = served
    request = urllib.request.Request(base + "/api/state", headers={"Host": "evil.example"})
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request)
    assert error.value.code == 403


def test_only_loopback_binding_and_nothing_written(tmp_path):
    for host in ("0.0.0.0", "", "192.168.1.5", "localhost"):
        with pytest.raises(ValueError, match="only binds"):
            dashboard.DashboardServer(tmp_path, host, 0)
    assert dashboard.main(["--host", "0.0.0.0", "--run-root", str(tmp_path)]) == 2


def test_serving_never_writes_under_the_run_root(served):
    server, base = served
    write_csv(server.state.run_root, 3)
    before = sorted((p, p.stat().st_mtime_ns) for p in server.state.run_root.rglob("*"))
    get(base, "/api/state")
    urllib.request.urlopen(base + "/").read()
    assert sorted((p, p.stat().st_mtime_ns) for p in server.state.run_root.rglob("*")) == before


def test_csv_module_header_matches_fields():
    assert FIELDS[-1] == "wall_time"
    assert next(csv.reader([",".join(FIELDS)])) == list(FIELDS)


def test_missing_train_csv_gives_empty_train(served):
    server, base = served
    write_csv(server.state.run_root, 2)
    state = get(base, "/api/state?since=0&train_since=0")
    assert state["train"] == [] and state["total_train_rows"] == 0
    assert state["total_episodes"] == 2


def test_train_rows_are_parsed_and_paged_with_train_since(served):
    server, base = served
    write_train(server.state.run_root, 5)
    state = get(base, "/api/state")
    assert state["total_train_rows"] == 5 and state["total_episodes"] == 0
    row = state["train"][2]
    assert row["index"] == 2 and row["timesteps"] == 6144 and row["rollout_index"] == 3
    assert row["explained_variance"] == 0.5 and row["use_none"] == 1.0
    assert row["wall_time"].startswith("2026-10-22")
    later = get(base, "/api/state?since=0&train_since=3")
    assert [r["index"] for r in later["train"]] == [3, 4] and later["total_train_rows"] == 5
    assert get(base, "/api/state?train_since=99")["train"] == []
    assert get(base, "/api/state?train_since=junk")["total_train_rows"] == 5


def test_train_partial_line_empty_values_and_truncation(served):
    server, base = served
    path = write_train(server.state.run_root, 2, tail=train_line(2)[:30])
    assert get(base, "/api/state")["total_train_rows"] == 2
    with path.open("a", encoding="utf-8") as handle:
        handle.write(train_line(2)[30:] + train_line(3, approx_kl="") + "a,b\n")
    state = get(base, "/api/state?train_since=2")
    assert state["total_train_rows"] == 4 and state["train"][1]["approx_kl"] is None
    write_train(server.state.run_root, 1)  # shorter file restarts from zero
    assert get(base, "/api/state?train_since=4")["total_train_rows"] == 1
    path.unlink()
    assert get(base, "/api/state")["total_train_rows"] == 0


def test_train_row_cap(served, monkeypatch):
    server, base = served
    write_train(server.state.run_root, 12)
    monkeypatch.setattr(dashboard, "MAX_ROWS", 5)
    first = get(base, "/api/state?train_since=0")
    assert len(first["train"]) == 5 and first["total_train_rows"] == 12
    assert [r["index"] for r in get(base, "/api/state?train_since=10")["train"]] == [10, 11]


def test_new_episode_columns_are_parsed_and_empty_ones_are_null(served):
    server, base = served
    path = server.state.run_root / "metrics" / "episodes.csv"
    path.parent.mkdir(parents=True)
    path.write_text(
        ",".join(FIELDS) + "\n"
        + line(0, use_bomb=3, use_active=1, use_pillcard=0, half_hearts_lost=4,
               steps_to_first_exit=250, steps_to_first_damage="", col_stall=-5.0)
        + line(1),
        "utf-8",
    )  # fmt: skip
    first, second = get(base, "/api/state")["episodes"]
    assert first["use_bomb"] == 3 and first["half_hearts_lost"] == 4
    assert first["steps_to_first_exit"] == 250 and first["steps_to_first_damage"] is None
    assert first["col_stall"] == -5.0
    assert second["use_bomb"] is None and second["steps_to_first_exit"] is None


def test_page_has_no_hardcoded_run_name(served):
    server, base = served
    with urllib.request.urlopen(base + "/") as response:
        assert "pure-v1" not in response.read().decode()
