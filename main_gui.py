import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import Database
from data_export import export_orders, import_orders
from logger_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)


class DeliveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Быстрая доставка - учёт заказов")
        self.db = Database()
        self.statuses = ['новый', 'в доставке', 'выполнен', 'отменён']
        self.create_widgets()
        self.load_orders()

    def create_widgets(self):
        filter_frame = tk.Frame(self.root)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(filter_frame, text="Фильтр по статусу:").pack(side=tk.LEFT)

        self.filter_status = ttk.Combobox(filter_frame, values=['Все'] + self.statuses, state='readonly')
        self.filter_status.pack(side=tk.LEFT, padx=5)
        self.filter_status.set('Все')

        tk.Button(filter_frame, text="Применить", command=self.load_orders).pack(side=tk.LEFT, padx=5)

        columns = ('id', 'date', 'customer', 'status', 'total')
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings')
        for col, text in zip(columns, ['ID', 'Дата', 'Клиент', 'Статус', 'Сумма']):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="Добавить", command=self.add_order).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Редактировать", command=self.edit_order).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Удалить", command=self.delete_order).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Показать отчёт", command=self.show_report).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Экспорт", command=self.export_data).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Импорт", command=self.import_data).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Обновить", command=self.load_orders).pack(side=tk.LEFT, padx=2)

    def load_orders(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        status = self.filter_status.get()
        status_filter = None if status == 'Все' else status
        orders = self.db.get_orders(status=status_filter)

        for o in orders:
            self.tree.insert('', tk.END, values=(
                o['id'], o['order_date'], o['customer_name'],
                o['status'], f"{o['total']:.2f}"
            ))

    def get_selected_order_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите заказ")
            return None
        item = self.tree.item(selected[0])
        return item['values'][0]

    def add_order(self):
        self.open_order_form()

    def edit_order(self):
        order_id = self.get_selected_order_id()
        if order_id:
            self.open_order_form(order_id)

    def delete_order(self):
        order_id = self.get_selected_order_id()
        if order_id:
            if messagebox.askyesno("Подтверждение", "Удалить заказ?"):
                self.db.delete_order(order_id)
                self.load_orders()

    def open_order_form(self, order_id=None):
        form = tk.Toplevel(self.root)
        form.title("Редактирование заказа" if order_id else "Новый заказ")
        form.grab_set()

        tk.Label(form, text="Клиент:").grid(row=0, column=0, sticky='e', padx=5, pady=5)

        customers = self.db.get_customers()
        customer_names = [f"{c['id']}: {c['name']}" for c in customers]
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(form, values=customer_names,
                                      textvariable=customer_var, state='readonly')
        customer_combo.grid(row=0, column=1, padx=5, pady=5)

        def add_new_customer():
            dlg = tk.Toplevel(form)
            dlg.title("Новый клиент")

            tk.Label(dlg, text="Имя:").grid(row=0, column=0)
            name_entry = tk.Entry(dlg)
            name_entry.grid(row=0, column=1)

            tk.Label(dlg, text="Телефон:").grid(row=1, column=0)
            phone_entry = tk.Entry(dlg)
            phone_entry.grid(row=1, column=1)

            tk.Label(dlg, text="Адрес:").grid(row=2, column=0)
            address_entry = tk.Entry(dlg)
            address_entry.grid(row=2, column=1)

            def save_customer():
                name = name_entry.get().strip()
                if not name:
                    messagebox.showerror("Ошибка", "Введите имя")
                    return
                cid = self.db.add_customer(
                    name,
                    phone_entry.get().strip(),
                    address_entry.get().strip()
                )
                dlg.destroy()
                updated = self.db.get_customers()
                names = [f"{c['id']}: {c['name']}" for c in updated]
                customer_combo['values'] = names
                for n in names:
                    if n.startswith(f"{cid}:"):
                        customer_var.set(n)
                        break

            tk.Button(dlg, text="Сохранить", command=save_customer).grid(
                row=3, column=0, columnspan=2, pady=5
            )

        tk.Button(form, text="Новый клиент", command=add_new_customer).grid(
            row=0, column=2, padx=5
        )

        tk.Label(form, text="Дата (ГГГГ-ММ-ДД):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        date_entry = tk.Entry(form)
        date_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form, text="Статус:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        status_combo = ttk.Combobox(form, values=self.statuses, state='readonly')
        status_combo.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form,
                 text="Товары (по одному в строке: название, количество, цена):"
                 ).grid(row=3, column=0, columnspan=2, sticky='w', padx=5, pady=5)

        items_text = tk.Text(form, width=50, height=8)
        items_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        if order_id:
            order = self.db.get_order(order_id)
            if order:
                for name in customer_names:
                    if name.startswith(f"{order['customer_id']}:"):
                        customer_var.set(name)
                        break
                date_entry.insert(0, order['order_date'])
                status_combo.set(order['status'])
                for item in order['items']:
                    items_text.insert(
                        tk.END,
                        f"{item['product_name']}, {item['quantity']}, {item['price']}\n"
                    )

        def save():
            try:
                if not customer_var.get():
                    raise ValueError("Выберите клиента")
                customer_id = int(customer_var.get().split(':')[0])

                order_date = date_entry.get().strip()
                if not order_date:
                    raise ValueError("Введите дату")

                status = status_combo.get()
                if status not in self.statuses:
                    raise ValueError("Выберите статус")

                items = []
                for line in items_text.get('1.0', tk.END).strip().split('\n'):
                    if not line.strip():
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) != 3:
                        raise ValueError(f"Неверный формат строки товара: {line}")
                    product_name = parts[0]
                    quantity = int(parts[1])
                    price = float(parts[2])
                    if quantity <= 0 or price < 0:
                        raise ValueError("Количество > 0, цена >= 0")
                    items.append({
                        'product_name': product_name,
                        'quantity': quantity,
                        'price': price
                    })

                if not items:
                    raise ValueError("Добавьте хотя бы один товар")

                if order_id:
                    self.db.update_order(order_id, customer_id, order_date, status, items)
                else:
                    self.db.add_order(customer_id, order_date, status, items)

                form.destroy()
                self.load_orders()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        tk.Button(form, text="Сохранить", command=save).grid(
            row=5, column=0, columnspan=2, pady=10
        )

    def show_report(self):
        report_win = tk.Toplevel(self.root)
        report_win.title("Отчёт")

        text = tk.Text(report_win, width=60, height=20)
        text.pack(padx=10, pady=10)

        status_counts = self.db.get_status_counts()
        text.insert(tk.END, "Количество заказов по статусам:\n")
        for status in self.statuses:
            text.insert(tk.END, f"  {status}: {status_counts.get(status, 0)}\n")

        text.insert(tk.END, "\nТоп-3 клиента по сумме заказов:\n")
        top = self.db.get_top_customers(3)
        if top:
            for i, c in enumerate(top, 1):
                text.insert(tk.END, f"  {i}. {c['name']} — {c['total_sum']:.2f}\n")
        else:
            text.insert(tk.END, "  нет данных\n")

        revenue_month = self.db.get_revenue('month')
        text.insert(tk.END, f"\nВыручка за месяц: {revenue_month:.2f}\n")

        text.config(state='disabled')

    def export_data(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("XML", "*.xml")]
        )
        if filepath:
            try:
                count = export_orders(self.db, filepath)
                messagebox.showinfo("Экспорт", f"Экспортировано {count} заказов")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def import_data(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("XML", "*.xml")]
        )
        if filepath:
            try:
                count = import_orders(self.db, filepath)
                messagebox.showinfo("Импорт", f"Импортировано {count} заказов")
                self.load_orders()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def on_close(self):
        self.db.close()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = DeliveryApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
