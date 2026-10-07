import pytest
import os
import tempfile
from database import Database


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    database = Database(path)
    yield database
    database.close()
    os.unlink(path)


def test_customer_crud(db):
    cid = db.add_customer("Иван", "+7", "Адрес")
    assert cid > 0

    c = db.get_customer(cid)
    assert c['name'] == "Иван"

    db.update_customer(cid, "Пётр", "+8", "Новый")
    c = db.get_customer(cid)
    assert c['name'] == "Пётр"

    db.delete_customer(cid)
    assert db.get_customer(cid) is None


def test_delete_customer_with_orders(db):
    cid = db.add_customer("Иван")
    db.add_order(cid, "2025-01-01", "новый", [
        {"product_name": "Пицца", "quantity": 1, "price": 500}
    ])
    with pytest.raises(ValueError):
        db.delete_customer(cid)


def test_order_crud_and_reports(db):
    cid = db.add_customer("Иван")
    oid = db.add_order(cid, "2025-01-01", "новый", [
        {"product_name": "Пицца", "quantity": 2, "price": 750}
    ])

    order = db.get_order(oid)
    assert order['total'] == 1500
    assert len(order['items']) == 1

    db.update_order(oid, cid, "2025-01-02", "выполнен", [
        {"product_name": "Кола", "quantity": 1, "price": 100}
    ])
    order = db.get_order(oid)
    assert order['status'] == "выполнен"
    assert order['total'] == 100

    counts = db.get_status_counts()
    assert counts.get("выполнен") == 1

    top = db.get_top_customers(3)
    assert top[0]['name'] == "Иван"

    rev = db.get_revenue('month')
    assert rev >= 0

    db.delete_order(oid)
    assert db.get_order(oid) is None
