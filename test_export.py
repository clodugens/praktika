import pytest
import os
import tempfile
from database import Database
from data_export import export_orders, import_orders


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    database = Database(path)
    yield database
    database.close()
    os.unlink(path)


def test_export_import_json(db):
    cid = db.add_customer("Иван", "+7", "Адрес")
    db.add_order(cid, "2025-01-01", "новый", [
        {"product_name": "Пицца", "quantity": 2, "price": 750}
    ])

    fd, json_path = tempfile.mkstemp(suffix='.json')
    os.close(fd)

    try:
        count = export_orders(db, json_path)
        assert count == 1

        db2 = Database(db.db_path + ".2")
        imported = import_orders(db2, json_path)
        assert imported == 1

        orders = db2.get_orders()
        assert len(orders) == 1

        db2.close()
        os.unlink(db.db_path + ".2")
    finally:
        os.unlink(json_path)


def test_export_import_xml(db):
    cid = db.add_customer("Иван", "+7", "Адрес")
    db.add_order(cid, "2025-01-01", "новый", [
        {"product_name": "Пицца", "quantity": 2, "price": 750}
    ])

    fd, xml_path = tempfile.mkstemp(suffix='.xml')
    os.close(fd)

    try:
        count = export_orders(db, xml_path)
        assert count == 1

        db2 = Database(db.db_path + ".3")
        imported = import_orders(db2, xml_path)
        assert imported == 1

        orders = db2.get_orders()
        assert len(orders) == 1

        db2.close()
        os.unlink(db.db_path + ".3")
    finally:
        os.unlink(xml_path)
