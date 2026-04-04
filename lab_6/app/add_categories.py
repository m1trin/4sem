# add_categories.py
import sys
import os

# Добавляем текущую папку в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Category

print("=" * 50)
print("Добавление категорий в базу данных")
print("=" * 50)

with app.app_context():
    # Проверяем, есть ли уже категории
    existing = db.session.execute(db.select(Category)).scalars().all()
    
    if existing:
        print(f"\nВ базе уже есть {len(existing)} категорий:")
        for cat in existing:
            print(f"  ✓ {cat.name}")
    else:
        # Список категорий
        categories_list = ['Программирование', 'Математика', 'Языкознание']
        
        print("\nДобавление категорий:")
        for cat_name in categories_list:
            category = Category(name=cat_name)
            db.session.add(category)
            print(f"  + {cat_name}")
        
        db.session.commit()
        print("\n✅ Категории успешно добавлены!")
        
        # Показываем результат
        print("\nТекущий список категорий:")
        categories = db.session.execute(db.select(Category)).scalars().all()
        for cat in categories:
            print(f"  {cat.id}. {cat.name}")
    
    print("\n" + "=" * 50)
    print("Готово!")