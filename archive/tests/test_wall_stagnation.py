import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from test_checkpoint_policy import CFG_HASH, RAW_CONFIG, SEED, observations, synthetic_env

from isaac_threrisaifuture.wall_stagnation import (
    MASK_OFFSET,
    ReplayError,
    TracePair,
    _enemy_x_indices,
    _potentials,
    main,
    policy_probabilities,
    probe_inputs,
    read_pairs,
    replay,
    summarize,
    verify_manifest,
)

FIXTURE = Path(__file__).parent / "fixtures" / "wall_stagnation"
# Logged firing_position_reward bonuses (run/live-events.jsonl) for records 30-38.
LOGGED = {
    79472: 0.0,
    79477: 0.0,
    79480: 0.0,
    79483: 0.0,
    79486: 0.0,
    79489: 0.0006669704073344468,
    79492: 0.0009969575799480546,
    79495: -0.0002216861175193402,
    79498: -0.0014427592393917998,
}


def _lines(name: str) -> list[str]:
    return (FIXTURE / name).read_text(encoding="utf-8").splitlines()


def _write(path: Path, lines: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _pairs() -> list[TracePair]:
    return read_pairs(FIXTURE / "policy.jsonl", FIXTURE / "oracle.jsonl")


def test_fixture_replay_reproduces_logged_shaping_and_target_switch() -> None:
    pairs = _pairs()
    rows = replay(pairs, LOGGED)

    assert [r["record_id"] for r in rows] == list(range(30, 39))
    assert all(r["bonus"] == r["logged_bonus"] for r in rows)
    assert all(r["encoding_matches"] for r in rows)
    assert {r["segment"] for r in rows} == {0}
    switch = next(r for r in rows if r["record_id"] == 33)
    assert switch["target_id"] == 2 and switch["bonus"] == 0.0
    # At the left wall v4 has no interior potential; v5 links to boundary patch 17.
    assert all(r["phi_v4"] is None and r["phi_v5"] is not None for r in rows)
    assert {r["support_patch"] for r in rows} == {17}
    # A right-then-back deviation is zero-sum by design, so it is not reinforced.
    deviation = [r["bonus"] for r in rows if 35 <= r["record_id"] <= 38]
    assert deviation[0] > 0 and deviation[1] > 0
    assert abs(sum(deviation)) < 1e-5

    targets = summarize(pairs, rows, wall=(70.0, 209.35))["targets"]
    assert targets["target_switches"] == [[33, 1, 2]]
    assert targets["last_listed"]["1"] == [32, 3.0]


def test_chain_break_starts_a_new_segment() -> None:
    pairs = _pairs()
    keep = [0, 1, 2, 4, 5]  # record 33 removed, so 34 does not continue from 32
    rows = replay([pairs[i] for i in keep], None)
    assert [r["segment"] for r in rows] == [0, 0, 0, 1, 1]
    assert all(r["logged_bonus"] is None for r in rows)


@pytest.mark.parametrize("case", ["short_oracle", "not_increasing", "ids_differ"])
def test_pairing_rejects_unpaired_or_reordered_records(tmp_path: Path, case: str) -> None:
    policy, oracle = _lines("policy.jsonl"), _lines("oracle.jsonl")
    swapped = [oracle[1], oracle[0], *oracle[2:]]
    if case == "short_oracle":
        oracle = oracle[:-1]
    elif case == "not_increasing":
        policy, oracle = [policy[1], policy[0], *policy[2:]], swapped
    else:
        oracle = swapped
    with pytest.raises((ReplayError, ValueError)):
        read_pairs(_write(tmp_path / "p.jsonl", policy), _write(tmp_path / "o.jsonl", oracle))


@pytest.mark.parametrize("field", ["selected_action", "session_id"])
def test_pairing_rejects_invalid_action_or_identity(tmp_path: Path, field: str) -> None:
    policy = _lines("policy.jsonl")
    record = json.loads(policy[0])
    if field == "selected_action":
        record["selected_action"] = [5, 0]
    else:
        record["before"]["session_id"] = "other-session"
    policy[0] = json.dumps(record)
    with pytest.raises(ReplayError):
        read_pairs(_write(tmp_path / "p.jsonl", policy), FIXTURE / "oracle.jsonl")


def test_record_cap_is_enforced() -> None:
    with pytest.raises(ReplayError, match="exceeds 3 records"):
        read_pairs(FIXTURE / "policy.jsonl", FIXTURE / "oracle.jsonl", max_records=3)


def _bundle(root: Path) -> Path:
    _write(root / "traces/learning-policy.jsonl", _lines("policy.jsonl"))
    _write(root / "traces/learning-oracle.jsonl", _lines("oracle.jsonl"))
    events = [
        json.dumps({"event": "firing_position_reward", "data": {"frame_id": f, "bonus": b}})
        for f, b in LOGGED.items()
    ]
    _write(root / "run/live-events.jsonl", events)
    _write(root / "run/phases.json", [json.dumps({"phases": [{"phase": "learning"}]})])
    files = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        data = path.read_bytes()
        files[path.relative_to(root).as_posix()] = {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    _write(root / "MANIFEST.json", [json.dumps({"bundle_id": "fixture", "files": files})])
    return root


def test_manifest_detects_tampering(tmp_path: Path) -> None:
    root = _bundle(tmp_path / "bundle")
    assert verify_manifest(root)["verified_files"] == 4
    events = root / "run/live-events.jsonl"
    events.write_text(events.read_text(encoding="utf-8").replace("0.0009", "0.0019"))
    with pytest.raises(ReplayError, match="Manifest mismatch"):
        verify_manifest(root)


def test_cli_writes_replay_without_checkpoint_and_never_overwrites(tmp_path: Path) -> None:
    root = _bundle(tmp_path / "bundle")
    output = tmp_path / "out"
    assert main(["--bundle", str(root), "--output", str(output)]) == 0
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["shaping_replay"] == {"compared": 9, "missing_log": 0, "mismatches": 0}
    assert summary["encoding_matches"] == 9
    assert summary["frozen_policy_audit"].startswith("not_run")
    assert len((output / "rows.jsonl").read_text(encoding="utf-8").splitlines()) == 9
    with pytest.raises(SystemExit):
        main(["--bundle", str(root), "--output", str(output)])


def test_probe_inputs_change_only_intended_features() -> None:
    observations = np.stack([p.observation for p in _pairs()])
    probes = probe_inputs(observations, start=3)
    assert probes["recorded"] is observations
    for name, columns in (
        ("mirror_enemy_x", _enemy_x_indices()),
        ("movement_unknown", list(range(MASK_OFFSET, MASK_OFFSET + 8))),
    ):
        changed = np.argwhere(probes[name] != observations)
        assert changed.size and (changed[:, 0] >= 3).all()
        assert set(changed[:, 1].tolist()) <= set(columns)


@pytest.mark.parametrize("change", ["unclear", "unknown", "other_source"])
def test_wall_potential_refuses_unsupported_boundary_geometry(change: str) -> None:
    after = _pairs()[3].after  # record 33: first state with only target 2, at the wall
    assert after.oracle and after.oracle.firing and after.oracle.firing.boundary_support
    support = after.oracle.firing.boundary_support
    if change == "other_source":
        moved = support.source.model_copy(update={"x": support.source.x + 1.0})
        support = support.model_copy(update={"source": moved})
    else:
        support = support.model_copy(update={"clear": False if change == "unclear" else None})
    firing = after.oracle.firing.model_copy(update={"boundary_support": support})
    oracle = after.oracle.model_copy(update={"firing": firing})
    assert _potentials(after)[1] is not None
    assert _potentials(after.model_copy(update={"oracle": oracle})) == (None, None)


def test_frozen_probabilities_carry_state_and_leave_checkpoint_unchanged(
    tmp_path: Path,
) -> None:
    from isaac_threrisaifuture.training import TrainingConfig, train

    config = TrainingConfig.model_validate(RAW_CONFIG)
    result = train(config, CFG_HASH, seed=SEED, env_factory=synthetic_env, out_dir=tmp_path)
    assert result.checkpoint_id is not None
    trained = tmp_path / "checkpoints" / result.checkpoint_id
    from isaac_threrisaifuture.checkpoint_policy import CheckpointPolicy
    from isaac_threrisaifuture.checkpoints import CheckpointError

    inputs = np.stack(observations(12, seed=3))
    before = {p.name: p.read_bytes() for p in trained.iterdir() if p.is_file()}
    identity, probs = policy_probabilities(trained, CFG_HASH, SEED, inputs)

    reference = CheckpointPolicy(trained, expected_config_hash=CFG_HASH, expected_seed=SEED)
    reference.reset(0)
    actions = [reference.act(obs).tolist() for obs in inputs]
    assert identity == reference.identity.to_dict()
    assert np.allclose(probs[:, :5].sum(1), 1) and np.allclose(probs[:, 5:].sum(1), 1)
    assert [[int(p[:5].argmax()), int(p[5:].argmax())] for p in probs] == actions
    assert {p.name: p.read_bytes() for p in trained.iterdir() if p.is_file()} == before
    with pytest.raises(CheckpointError):
        policy_probabilities(trained, "0" * 64, SEED, inputs)
