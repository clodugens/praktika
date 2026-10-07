 Быстрая доставка — учёт заказов

Внутреннее приложение для учёта заказов. Поддерживает CLI и GUI, базу данных SQLite, экспорт и импорт заказов в форматах JSON и XML, логирование и фильтрацию.

 Возможности

- Управление клиентами (CRUD). Нельзя удалить клиента, если у него есть заказы.
- Управление заказами (CRUD) со статусами: новый, в доставке, выполнен, отменён.
- Фильтрация заказов по статусу и дате.
- Отчёты: количество заказов по статусам, топ-3 клиента по сумме, выручка за день/неделю/месяц.
- Экспорт и импорт заказов в JSON и XML с валидацией.
- CLI через argparse и GUI на Tkinter.
- Логирование в файл и консоль.

 Структура проекта

delivery_system/
├── main_cli.py
├── main_gui.py
├── database.py
├── models.py
├── data_export.py
├── logger_config.py
├── tests/
│   ├── test_database.py
│   ├── test_models.py
│   └── test_export.py
├── logs/
├── data/
├── requirements.txt
└── README.md

 Установка

pip install -r requirements.txt

 Запуск CLI

python main_cli.py report --period month
python main_cli.py export --file orders.xml
python main_cli.py export --file orders.json
python main_cli.py import --file orders.xml
python main_cli.py import --file orders.json

 Запуск GUI

python main_gui.py

 Запуск тестов

pytest

 Технологии

- Python 3.8+
- SQLite (sqlite3)
- Tkinter
- argparse
- logging
- xml.etree.ElementTree и json
- pytest
