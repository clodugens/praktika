import sqlite3
import os
from datetime import datetime, timedelta
import logging

DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'delivery.db')


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.logger = logging.getLogger(__name__)

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                address TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('новый','в доставке','выполнен','отменён')),
                total REAL NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def add_customer(self, name, phone='', address=''):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
                    (name, phone, address))
        self.conn.commit()
        return cur.lastrowid

    def get_customers(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM customers ORDER BY name")
        return [dict(row) for row in cur.fetchall()]

    def get_customer(self, customer_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_customer(self, customer_id, name, phone='', address=''):
        cur = self.conn.cursor()
        cur.execute("UPDATE customers SET name=?, phone=?, address=? WHERE id=?",
                    (name, phone, address, customer_id))
        self.conn.commit()
        return cur.rowcount > 0

    def delete_customer(self, customer_id):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE customer_id = ?", (customer_id,))
        count = cur.fetchone()[0]
        if count > 0:
            raise ValueError("Нельзя удалить клиента: у него есть заказы")
        cur.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def add_order(self, customer_id, order_date, status, items):
        if status not in ('новый', 'в доставке', 'выполнен', 'отменён'):
            raise ValueError("Недопустимый статус")
        total = sum(item['quantity'] * item['price'] for item in items)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO orders (customer_id, order_date, status, total) VALUES (?, ?, ?, ?)",
            (customer_id, order_date, status, total)
        )
        order_id = cur.lastrowid
        for item in items:
            cur.execute(
                "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, item['product_name'], item['quantity'], item['price'])
            )
        self.conn.commit()
        return order_id

    def get_orders(self, status=None, date_from=None, date_to=None):
        query = """
            SELECT o.id, o.order_date, o.status, o.total,
                   c.name AS customer_name, c.id AS customer_id
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND o.status = ?"
            params.append(status)
        if date_from:
            query += " AND o.order_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND o.order_date <= ?"
            params.append(date_to)
        query += " ORDER BY o.order_date DESC, o.id DESC"
        cur = self.conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def get_order(self, order_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT o.id, o.customer_id, o.order_date, o.status, o.total,
                   c.name AS customer_name
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = ?
        """, (order_id,))
        order = cur.fetchone()
        if not order:
            return None
        order_dict = dict(order)
        cur.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        order_dict['items'] = [dict(row) for row in cur.fetchall()]
        return order_dict

    def update_order(self, order_id, customer_id, order_date, status, items):
        if status not in ('новый', 'в доставке', 'выполнен', 'отменён'):
            raise ValueError("Недопустимый статус")
        total = sum(item['quantity'] * item['price'] for item in items)
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE orders SET customer_id=?, order_date=?, status=?, total=? WHERE id=?",
            (customer_id, order_date, status, total, order_id)
        )
        cur.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        for item in items:
            cur.execute(
                "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, item['product_name'], item['quantity'], item['price'])
            )
        self.conn.commit()
        return cur.rowcount > 0

    def delete_order(self, order_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_status_counts(self):
        cur = self.conn.cursor()
        cur.execute("SELECT status, COUNT(*) as count FROM orders GROUP BY status")
        return {row['status']: row['count'] for row in cur.fetchall()}

    def get_top_customers(self, limit=3):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT c.name, SUM(o.total) as total_sum
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.status != 'отменён'
            GROUP BY c.id
            ORDER BY total_sum DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]

    def get_revenue(self, period='month'):
        now = datetime.now()
        if period == 'day':
            start = now.strftime('%Y-%m-%d')
        elif period == 'week':
            start = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        elif period == 'month':
            start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
        else:
            raise ValueError("Период должен быть day, week или month")
        cur = self.conn.cursor()
        cur.execute("""
            SELECT SUM(total) as revenue
            FROM orders
            WHERE order_date >= ? AND status != 'отменён'
        """, (start,))
        row = cur.fetchone()
        return row['revenue'] if row['revenue'] else 0.0

    def get_all_data(self):
        customers = self.get_customers()
        orders = []
        for o in self.get_orders():
            full = self.get_order(o['id'])
            if full:
                orders.append(full)
        return {'customers': customers, 'orders': orders}
