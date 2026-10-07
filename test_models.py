from models import OrderItem, Order


def test_order_item_total():
    item = OrderItem("Пицца", 2, 750)
    assert item.total == 1500


def test_order_calculate_total():
    order = Order(items=[
        OrderItem("Пицца", 2, 750),
        OrderItem("Кола", 1, 100)
    ])
    assert order.calculate_total() == 1600
