import argparse
import sys
from database import Database
from data_export import export_orders, import_orders
from logger_config import setup_logging


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description='Быстрая доставка - CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)

    report_parser = subparsers.add_parser('report', help='Показать отчёт')
    report_parser.add_argument('--period', choices=['day', 'week', 'month'],
                               default='month', help='Период для выручки')

    export_parser = subparsers.add_parser('export', help='Экспорт заказов')
    export_parser.add_argument('--file', required=True,
                               help='Файл для экспорта (.xml или .json)')

    import_parser = subparsers.add_parser('import', help='Импорт заказов')
    import_parser.add_argument('--file', required=True,
                               help='Файл для импорта (.xml или .json)')

    args = parser.parse_args()

    db = Database()
    try:
        if args.command == 'report':
            status_counts = db.get_status_counts()
            print("Количество заказов по статусам:")
            for status in ['новый', 'в доставке', 'выполнен', 'отменён']:
                print(f"  {status}: {status_counts.get(status, 0)}")

            print("\nТоп-3 клиента по сумме заказов:")
            top = db.get_top_customers(3)
            if top:
                for i, c in enumerate(top, 1):
                    print(f"  {i}. {c['name']} — {c['total_sum']:.2f}")
            else:
                print("  нет данных")

            revenue = db.get_revenue(args.period)
            print(f"\nОбщая выручка за период ({args.period}): {revenue:.2f}")

        elif args.command == 'export':
            count = export_orders(db, args.file)
            print(f"Экспортировано {count} заказов в {args.file}")

        elif args.command == 'import':
            count = import_orders(db, args.file)
            print(f"Импортировано {count} заказов из {args.file}")

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
