# setup.py
from app import app
from models import db

print("Инициализация базы данных...")

with app.app_context():
    # Создаем все таблицы
    db.create_all()
    print("✓ Таблицы успешно созданы!")
    
    # Проверяем созданные таблицы
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\nСозданные таблицы:")
    for table in tables:
        print(f"  - {table}")
    
    # Проверяем наличие таблицы reviews
    if 'reviews' in tables:
        print("\n✓ Таблица 'reviews' создана!")
    else:
        print("\n✗ Таблица 'reviews' не найдена")