from dataclasses import dataclass, field
from typing import List

@dataclass
class Customer:
    id: int = None
    name: str = ""
    phone: str = ""
    address: str = ""

@dataclass
class OrderItem:
    product_name: str
    quantity: int
    price: float

    @property
    def total(self):
        return self.quantity * self.price

@dataclass
class Order:
    id: int = None
    customer_id: int = None
    order_date: str = ""
    status: str = "новый"
    items: List[OrderItem] = field(default_factory=list)
    total: float = 0.0

    def calculate_total(self):
        self.total = sum(item.total for item in self.items)
        return self.total
