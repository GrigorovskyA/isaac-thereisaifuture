import pytest

from isaac_threrisaifuture.resources import (
    Offer,
    RandomChooser,
    ResourceEvent,
    ResourceLedger,
    ResourceState,
    evaluate_build,
)


def ev(kind, resource, entity=1, gen=1, visit=1, amount=1.0, item=None, session="s"):
    return ResourceEvent(kind, session, visit, entity, gen, resource, amount, item)


def ledger(**kw) -> ResourceLedger:
    lg = ResourceLedger()
    lg.reset("s", ResourceState(max_hearts=6.0, **kw))
    return lg


def test_drop_and_repick_item_pays_once() -> None:
    lg = ledger()
    first = lg.consume([ev("pickup", "item", 1, item="x")])
    lg.consume([ev("drop", "item", 1, item="x")])
    again = lg.consume([ev("pickup", "item", 2, gen=2, item="x")])
    assert first > 0 and again == 0
    assert "x" in lg.state.inventory


def test_repeated_pickup_of_same_entity_pays_once() -> None:
    lg = ledger()
    a = lg.consume([ev("pickup", "coins", 5, amount=3)])
    b = lg.consume([ev("pickup", "coins", 5, amount=3)])
    assert a > 0 and b == 0 and lg.stats.ignored_duplicates == 1


def test_empty_use_and_spend_pay_nothing() -> None:
    lg = ledger(coins=5)
    assert lg.consume([ev("use", "item", amount=0, item="a"), ev("spend", "coins", amount=3)]) == 0
    assert lg.stats.empty_uses == 1 and lg.state.coins == 2


def test_healed_hp_reuse_pays_only_effective_heal() -> None:
    lg = ledger(hearts=6.0)
    assert lg.consume([ev("pickup", "hearts", 1, amount=2)]) == 0  # already full
    lg.consume([ev("damage", "hearts", amount=2)])
    assert lg.consume([ev("pickup", "hearts", 2, amount=2)]) == pytest.approx(0.2)
    assert lg.state.hearts == 6.0


def test_episode_cap_and_session_check() -> None:
    lg = ledger()
    total = sum(lg.consume([ev("pickup", "item", i, item=f"i{i}")]) for i in range(100))
    assert total == pytest.approx(5.0)
    with pytest.raises(ValueError):
        lg.consume([ev("pickup", "coins", session="other")])


def test_random_chooser_is_affordable_and_seeded() -> None:
    offers = [Offer(1, "a", 5), Offer(2, "b", 50)]
    st = ResourceState(coins=10)
    assert {RandomChooser(1).choose(st, offers) for _ in range(5)} == {0}
    assert RandomChooser(1).choose(ResourceState(), offers) == -1


def test_counterfactual_evaluation_is_fixed_and_offline() -> None:
    calls: list[tuple[tuple[str, ...], str]] = []

    def run(build, scenario):
        calls.append((build, scenario))
        return float(len(build))

    res = evaluate_build(["a", "b"], ["s1", "s2"], run)
    assert res.mean == 2.0 and calls == [(("a", "b"), "s1"), (("a", "b"), "s2")]
