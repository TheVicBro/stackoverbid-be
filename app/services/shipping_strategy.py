from abc import ABC, abstractmethod


class ShippingStrategy(ABC):

    @abstractmethod
    def calculate(self, base_price, item):
        pass

    @abstractmethod
    def estimated_days(self, item):
        pass


class StandardShipping(ShippingStrategy):

    def calculate(self, base_price, item):
        return base_price

    def estimated_days(self, item):
        return item.shipping_time_days


class ExpeditedShipping(ShippingStrategy):

    def calculate(self, base_price, item):
        return base_price + item.expedited_shipping_cost

    def estimated_days(self, item):
        return max(1, item.shipping_time_days // 2)


def get_shipping_strategy(expedited):
    if expedited:
        return ExpeditedShipping()
    return StandardShipping()
