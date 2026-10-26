"""Offline tests for scripts/lua_perf.py on a synthetic Isaac log."""

import importlib.util
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lua_perf", ROOT / "scripts/lua_perf.py")
assert spec and spec.loader
lua_perf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lua_perf)

PREFIX = "[Isaac Future Observer] Observer perf "
LOG = [
    "Lua Debug: something else",
    "[Isaac Future Observer] session marker",
    PREFIX + "window_ms=10000 updates=300 renders=600 snapshots=200 update_ms=100"
    " render_ms=4000 capture_ms=2000 encode_ms=500",
    "random noise",
    PREFIX + "window_ms=10000 updates=340 renders=600 snapshots=400 update_ms=300"
    " render_ms=6000 capture_ms=3000 encode_ms=1500",
    PREFIX + "window_ms=5 updates=1",  # incomplete line is ignored
]


def test_parse_line_requires_all_keys():
    assert lua_perf.parse_line(LOG[2]) is not None
    assert lua_perf.parse_line(LOG[0]) is None
    assert lua_perf.parse_line(LOG[5]) is None


def test_summary_rates_and_shares():
    stats = lua_perf.summarize(lua_perf.read_windows(LOG))
    assert stats["windows"] == 2
    assert stats["updates_per_s"] == 32
    assert stats["renders_per_s"] == 60
    assert stats["snapshots_per_s"] == 30
    assert math.isclose(stats["update_share"], 0.02)
    assert math.isclose(stats["render_share"], 0.5)
    assert math.isclose(stats["capture_share"], 0.25)
    assert math.isclose(stats["encode_share"], 0.1)
    assert math.isclose(stats["capture_ms_per_snapshot"], 5000 / 600)
    assert math.isclose(stats["encode_ms_per_snapshot"], 2000 / 600)


def test_since_keeps_only_later_windows():
    assert len(lua_perf.read_windows(LOG, "session marker")) == 2
    assert len(lua_perf.read_windows(LOG, "noise")) == 1


def test_cli_prints_summary_and_fails_without_windows(tmp_path, monkeypatch, capsys):
    log = tmp_path / "log.txt"
    log.write_text("\n".join(LOG), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["lua_perf.py", str(log)])
    assert lua_perf.main() == 0
    assert "updates/s          32.0" in capsys.readouterr().out
    log.write_text("nothing here\n", encoding="utf-8")
    assert lua_perf.main() == 1
