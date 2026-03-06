"""
Strategy pattern: shipping cost calculation.
Different strategies for standard vs expedited shipping; payment service uses the selected strategy.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import models


class ShippingCostStrategy(ABC):
    """Strategy for computing the additional shipping cost for an item."""

    @abstractmethod
    def get_shipping_cost(self, item: "models.Item") -> float:
        """Return the shipping cost to add to the item price."""
        pass


class StandardShippingStrategy(ShippingCostStrategy):
    """Standard shipping: no extra cost (included in listing)."""

    def get_shipping_cost(self, item: "models.Item") -> float:
        return 0.0


class ExpeditedShippingStrategy(ShippingCostStrategy):
    """Expedited shipping: add the item's expedited_shipping_cost."""

    def get_shipping_cost(self, item: "models.Item") -> float:
        return float(item.expedited_shipping_cost)
