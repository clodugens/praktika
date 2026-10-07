import json
import xml.etree.ElementTree as ET
import os
import logging

logger = logging.getLogger(__name__)


def export_orders(db, filepath):
    data = db.get_all_data()
    export_data = {'orders': []}

    for order in data['orders']:
        customer = next((c for c in data['customers'] if c['id'] == order['customer_id']), None)
        if not customer:
            continue
        export_data['orders'].append({
            'id': order['id'],
            'customer': {
                'name': customer['name'],
                'phone': customer['phone'],
                'address': customer['address']
            },
            'order_date': order['order_date'],
            'status': order['status'],
            'total': order['total'],
            'items': order['items']
        })

    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.json':
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=4)

    elif ext == '.xml':
        root = ET.Element('orders')
        for order in export_data['orders']:
            order_el = ET.SubElement(root, 'order', id=str(order['id']))

            cust_el = ET.SubElement(order_el, 'customer')
            ET.SubElement(cust_el, 'name').text = order['customer']['name']
            ET.SubElement(cust_el, 'phone').text = order['customer']['phone'] or ''
            ET.SubElement(cust_el, 'address').text = order['customer']['address'] or ''

            ET.SubElement(order_el, 'order_date').text = order['order_date']
            ET.SubElement(order_el, 'status').text = order['status']
            ET.SubElement(order_el, 'total').text = str(order['total'])

            items_el = ET.SubElement(order_el, 'items')
            for item in order['items']:
                item_el = ET.SubElement(items_el, 'item')
                ET.SubElement(item_el, 'product_name').text = item['product_name']
                ET.SubElement(item_el, 'quantity').text = str(item['quantity'])
                ET.SubElement(item_el, 'price').text = str(item['price'])

        tree = ET.ElementTree(root)
        tree.write(filepath, encoding='utf-8', xml_declaration=True)

    else:
        raise ValueError("Поддерживаются только .json и .xml")

    logger.info(f"Экспортировано {len(export_data['orders'])} заказов в {filepath}")
    return len(export_data['orders'])


def import_orders(db, filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.json':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        orders = data.get('orders', [])

    elif ext == '.xml':
        tree = ET.parse(filepath)
        root = tree.getroot()
        orders = []
        for order_el in root.findall('order'):
            order = {
                'customer': {
                    'name': order_el.findtext('customer/name', ''),
                    'phone': order_el.findtext('customer/phone', ''),
                    'address': order_el.findtext('customer/address', '')
                },
                'order_date': order_el.findtext('order_date', ''),
                'status': order_el.findtext('status', ''),
                'items': []
            }
            for item_el in order_el.findall('items/item'):
                order['items'].append({
                    'product_name': item_el.findtext('product_name', ''),
                    'quantity': int(item_el.findtext('quantity', '0')),
                    'price': float(item_el.findtext('price', '0.0'))
                })
            orders.append(order)
    else:
        raise ValueError("Поддерживаются только .json и .xml")

    imported = 0
    for order in orders:
        if not order.get('customer', {}).get('name'):
            raise ValueError("У заказа отсутствует имя клиента")
        if not order.get('order_date'):
            raise ValueError("У заказа отсутствует дата")
        if order.get('status') not in ('новый', 'в доставке', 'выполнен', 'отменён'):
            raise ValueError(f"Недопустимый статус: {order.get('status')}")
        if not isinstance(order.get('items'), list) or len(order['items']) == 0:
            raise ValueError("Заказ должен содержать хотя бы один товар")

        for item in order['items']:
            if not item.get('product_name'):
                raise ValueError("У товара отсутствует название")
            if not isinstance(item.get('quantity'), int) or item['quantity'] <= 0:
                raise ValueError("Количество должно быть положительным целым числом")
            if not isinstance(item.get('price'), (int, float)) or item['price'] < 0:
                raise ValueError("Цена должна быть неотрицательным числом")

        customer_id = None
        phone = order['customer'].get('phone', '')
        if phone:
            for c in db.get_customers():
                if c['phone'] == phone:
                    customer_id = c['id']
                    break

        if customer_id is None:
            customer_id = db.add_customer(
                order['customer']['name'],
                phone,
                order['customer'].get('address', '')
            )

        db.add_order(customer_id, order['order_date'], order['status'], order['items'])
        imported += 1

    logger.info(f"Импортировано {imported} заказов из {filepath}")
    return imported
