from dataclasses import dataclass

from app.services.shipping_strategy import (
    ExpeditedShipping,
    StandardShipping,
    get_shipping_strategy,
)


@dataclass
class FakeItem:
    current_price: float = 25.0
    shipping_time_days: int = 6
    expedited_shipping_cost: float = 12.0


def test_standard_shipping_no_surcharge():
    strategy = StandardShipping()
    item = FakeItem(current_price=50.0)
    assert strategy.calculate(50.0, item) == 50.0


def test_standard_shipping_days():
    strategy = StandardShipping()
    item = FakeItem(shipping_time_days=7)
    assert strategy.estimated_days(item) == 7


def test_expedited_shipping_adds_cost():
    strategy = ExpeditedShipping()
    item = FakeItem(current_price=50.0, expedited_shipping_cost=15.0)
    assert strategy.calculate(50.0, item) == 65.0


def test_expedited_shipping_halves_days():
    strategy = ExpeditedShipping()
    item = FakeItem(shipping_time_days=6)
    assert strategy.estimated_days(item) == 3


def test_expedited_shipping_minimum_one_day():
    strategy = ExpeditedShipping()
    item = FakeItem(shipping_time_days=1)
    assert strategy.estimated_days(item) == 1


def test_factory_returns_standard():
    strategy = get_shipping_strategy(expedited=False)
    assert isinstance(strategy, StandardShipping)


def test_factory_returns_expedited():
    strategy = get_shipping_strategy(expedited=True)
    assert isinstance(strategy, ExpeditedShipping)
