from abc import ABC, abstractmethod
from typing import Protocol


class ShippableItem(Protocol):
    shipping_time_days: int
    expedited_shipping_cost: float


class ShippingStrategy(ABC):

    @abstractmethod
    def calculate(self, base_price: float, item: ShippableItem) -> float: ...

    @abstractmethod
    def estimated_days(self, item: ShippableItem) -> int: ...


class StandardShipping(ShippingStrategy):

    def calculate(self, base_price: float, item: ShippableItem) -> float:
        return base_price

    def estimated_days(self, item: ShippableItem) -> int:
        return item.shipping_time_days


class ExpeditedShipping(ShippingStrategy):

    def calculate(self, base_price: float, item: ShippableItem) -> float:
        return base_price + item.expedited_shipping_cost

    def estimated_days(self, item: ShippableItem) -> int:
        return max(1, item.shipping_time_days // 2)


def get_shipping_strategy(expedited: bool) -> ShippingStrategy:
    if expedited:
        return ExpeditedShipping()
    return StandardShipping()
