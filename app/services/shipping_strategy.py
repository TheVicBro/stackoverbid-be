from abc import ABC, abstractmethod
from typing import Protocol


class ShippableItem(Protocol):
    """Duck-typed interface for any object with shipping attributes."""
    shipping_time_days: int
    expedited_shipping_cost: float


class ShippingStrategy(ABC):
    """Strategy interface for shipping cost calculation."""

    @abstractmethod
    def calculate(self, base_price: float, item: ShippableItem) -> float:
        """Return the total amount the buyer must pay (base price + shipping)."""

    @abstractmethod
    def estimated_days(self, item: ShippableItem) -> int:
        """Return the estimated shipping duration in days."""


class StandardShipping(ShippingStrategy):
    """Free standard shipping — no surcharge, uses the item's default shipping time."""

    def calculate(self, base_price: float, item: ShippableItem) -> float:
        return base_price

    def estimated_days(self, item: ShippableItem) -> int:
        return item.shipping_time_days


class ExpeditedShipping(ShippingStrategy):
    """Expedited shipping — adds the item's expedited cost and halves delivery time."""

    def calculate(self, base_price: float, item: ShippableItem) -> float:
        return base_price + item.expedited_shipping_cost

    def estimated_days(self, item: ShippableItem) -> int:
        return max(1, item.shipping_time_days // 2)


def get_shipping_strategy(expedited: bool) -> ShippingStrategy:
    """Factory: return the appropriate shipping strategy."""
    if expedited:
        return ExpeditedShipping()
    return StandardShipping()
