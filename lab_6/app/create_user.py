# create_user.py
from app import app
from models import db, User

print("Создание пользователя...")

with app.app_context():
    # Проверяем, есть ли уже пользователь с логином 'ivan'
    user = db.session.execute(db.select(User).filter_by(login='ivan')).scalar()
    
    if not user:
        user = User(
            first_name='Иван',
            last_name='Иванов',
            middle_name='Иванович',
            login='ivan'
        )
        user.set_password('ivan123')  # Исправлено: пароль без !
        db.session.add(user)
        db.session.commit()
        print("✓ Пользователь успешно создан!")
        print(f"  Логин: {user.login}")
        print(f"  Пароль: ivan123")  # Исправлено
        print(f"  Полное имя: {user.full_name}")
    else:
        print("Пользователь уже существует:")
        print(f"  Логин: {user.login}")
        print(f"  Пароль: ivan123")
        print(f"  Полное имя: {user.full_name}")
    
    # Показываем всех пользователей в базе
    print("\nВсе пользователи в базе данных:")
    users = db.session.execute(db.select(User)).scalars().all()
    for u in users:
        print(f"  - {u.login}: {u.full_name}")