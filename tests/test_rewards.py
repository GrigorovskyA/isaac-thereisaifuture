import pytest
from synthetic import event

from isaac_threrisaifuture.rewards import CombatCoefficients, RewardLedger

COEF = CombatCoefficients(2.0, 0.5, 8.0, -8.0, -25.0, -0.01)


def _spawn(hp: float = 10.0):
    return event("enemy_spawned", entity_id=1, spawn_generation=1, amount=hp)


def _hit(amount: float, frame: int):
    return event("enemy_damaged", frame, entity_id=1, spawn_generation=1, amount=amount)


def test_healed_hp_is_not_paid_twice() -> None:
    ledger = RewardLedger(COEF)
    ledger.reset(1)
    ledger.consume([_spawn()], 0)
    total = sum(ledger.consume([_hit(5, f)], 0)[0] for f in (2, 3, 4))
    assert total == pytest.approx(COEF.enemy_hp_fraction_total)


def test_duplicate_room_clear_pays_once() -> None:
    ledger = RewardLedger(COEF)
    ledger.reset(1)
    first, _ = ledger.consume([event("room_cleared")], 0)
    second, _ = ledger.consume([event("room_cleared")], 0)
    assert first == COEF.room_clear_first and second == 0.0


def test_unknown_enemy_damage_earns_nothing() -> None:
    ledger = RewardLedger(COEF)
    ledger.reset(1)
    assert ledger.consume([_hit(5, 2)], 0)[0] == 0.0
    assert ledger.ignored_events == 1


def test_time_cost_only_while_enemy_alive() -> None:
    ledger = RewardLedger(COEF)
    ledger.reset(1)
    assert ledger.consume([], 30)[0] == 0.0
    ledger.consume([_spawn()], 0)
    assert ledger.consume([], 30)[0] == pytest.approx(COEF.active_combat_second)


def test_bad_version_is_rejected(tmp_path) -> None:
    path = tmp_path / "r.yaml"
    path.write_text("reward_version: 2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        CombatCoefficients.load(path)
