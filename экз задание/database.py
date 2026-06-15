import os
import hashlib
from werkzeug.security import generate_password_hash
from flask import Flask
from models import db, Role, ReviewStatus, User, Genre, Book, Cover, Review

def create_cover_file(path, color, title):
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (300, 450), color=color)
        d = ImageDraw.Draw(img)
        d.rectangle([(10, 10), (290, 440)], outline=(255, 255, 255), width=3)
        # Draw simple text
        d.text((30, 50), title, fill=(255, 255, 255))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)
        
        # Calculate MD5 hash
        with open(path, 'rb') as f:
            file_bytes = f.read()
        return hashlib.md5(file_bytes).hexdigest()
    except Exception as e:
        print(f"Error creating cover file: {e}")
        return "placeholderhash"

def init_db(app):
    if 'sqlalchemy' not in app.extensions:
        db.init_app(app)
    with app.app_context():
        # Drop all and recreate to ensure clean database state for deployment/testing
        db.drop_all()
        db.create_all()
        
        # 1. Seed Roles
        roles_data = [
            {"id": 1, "name": "Администратор", "description": "Полные права на управление библиотекой (добавление, редактирование, удаление книг)."},
            {"id": 2, "name": "Модератор", "description": "Права на редактирование книг и модерацию рецензий (одобрение или отклонение)."},
            {"id": 3, "name": "Пользователь", "description": "Обычный пользователь с возможностью просмотра книг, написания отзывов и просмотра своих отзывов."}
        ]
        for r_dict in roles_data:
            role = Role(id=r_dict["id"], name=r_dict["name"], description=r_dict["description"])
            db.session.add(role)
        
        # 2. Seed Review Statuses
        statuses_data = [
            {"id": 1, "name": "На рассмотрении"},
            {"id": 2, "name": "Одобрена"},
            {"id": 3, "name": "Отклонена"}
        ]
        for s_dict in statuses_data:
            status = ReviewStatus(id=s_dict["id"], name=s_dict["name"])
            db.session.add(status)
            
        # 3. Seed Genres
        genres_data = [
            "Фантастика",
            "Роман",
            "Детектив",
            "Фэнтези",
            "Ужасы",
            "Поэзия",
            "Исторический роман",
            "Приключения",
            "Научно-популярная литература",
            "Драма"
        ]
        for g_name in genres_data:
            genre = Genre(name=g_name)
            db.session.add(genre)
            
        # 4. Seed Users (Admin, Moderator, User)
        users_data = [
            {
                "login": "admin",
                "password": "adminpass",
                "last_name": "Админов",
                "first_name": "Алексей",
                "middle_name": "Игоревич",
                "role_id": 1
            },
            {
                "login": "moderator",
                "password": "modpass",
                "last_name": "Модераторов",
                "first_name": "Дмитрий",
                "middle_name": "Сергеевич",
                "role_id": 2
            },
            {
                "login": "user",
                "password": "userpass",
                "last_name": "Пользователев",
                "first_name": "Иван",
                "middle_name": "Алексеевич",
                "role_id": 3
            }
        ]
        
        for u_dict in users_data:
            user = User(
                login=u_dict["login"],
                password_hash=generate_password_hash(u_dict["password"]),
                last_name=u_dict["last_name"],
                first_name=u_dict["first_name"],
                middle_name=u_dict["middle_name"],
                role_id=u_dict["role_id"]
            )
            db.session.add(user)
            
        db.session.flush() # ensure user IDs are flushed
        
        # 5. Generate cover images and seed books
        covers_folder = os.path.join(app.root_path, 'static', 'covers')
        os.makedirs(covers_folder, exist_ok=True)
        
        # Generate 3 covers
        hash1 = create_cover_file(os.path.join(covers_folder, "1.jpg"), (99, 102, 241), "Master and Margarita")
        hash2 = create_cover_file(os.path.join(covers_folder, "2.jpg"), (16, 185, 129), "Crime and Punishment")
        hash3 = create_cover_file(os.path.join(covers_folder, "3.jpg"), (244, 63, 94), "Dracula")
        
        # Add Books
        b1 = Book(
            id=1,
            title="Мастер и Маргарита",
            author="Михаил Булгаков",
            publisher="Художественная литература",
            year=1967,
            page_count=480,
            short_description="Фантастический роман Михаила Афанасьевича Булгакова, сочетающий элементы сатиры, мистики, философии и любовной драмы."
        )
        b2 = Book(
            id=2,
            title="Преступление и наказание",
            author="Федор Достоевский",
            publisher="Русский Вестник",
            year=1866,
            page_count=600,
            short_description="Социально-философский роман Фёдора Михайловича Достоевского, посвященный психологической драме и духовному перерождению Родиона Раскольникова."
        )
        b3 = Book(
            id=3,
            title="Дракула",
            author="Брэм Стокер",
            publisher="Archibald Constable & Co",
            year=1897,
            page_count=400,
            short_description="Готический роман ужасов ирландского писателя Брэма Стокера, заложивший основы современной литературы о вампирах."
        )
        
        db.session.add_all([b1, b2, b3])
        db.session.flush()
        
        # Associate genres (IDs: 1=Фантастика, 2=Роман, 3=Детектив, 5=Ужасы)
        g_fant = Genre.query.get(1)
        g_rom = Genre.query.get(2)
        g_det = Genre.query.get(3)
        g_horror = Genre.query.get(5)
        
        b1.genres.extend([g_fant, g_rom])
        b2.genres.extend([g_rom, g_det])
        b3.genres.extend([g_horror, g_fant])
        
        # Add Covers
        cov1 = Cover(id=1, file_name="1.jpg", mime_type="image/jpeg", md5_hash=hash1, book_id=1)
        cov2 = Cover(id=2, file_name="2.jpg", mime_type="image/jpeg", md5_hash=hash2, book_id=2)
        cov3 = Cover(id=3, file_name="3.jpg", mime_type="image/jpeg", md5_hash=hash3, book_id=3)
        db.session.add_all([cov1, cov2, cov3])
        
        # 6. Seed reviews (User IDs: 1=admin, 2=moderator, 3=user)
        reviews_data = [
            # Book 1: Мастер и Маргарита (2 approved reviews -> average rating (5+4)/2 = 4.5)
            {
                "book_id": 1,
                "user_id": 3,
                "rating": 5,
                "text": "Потрясающая книга! Одна из лучших в русской классике. Сочетание мистики, сатиры и глубоких философских вопросов завораживает.",
                "status_id": 2 # Одобрена
            },
            {
                "book_id": 1,
                "user_id": 2,
                "rating": 4,
                "text": "Очень интересный сюжет, хотя некоторые части кажутся перегруженными. В целом — шедевр.",
                "status_id": 2 # Одобрена
            },
            # Book 2: Преступление и наказание (1 approved, 1 pending)
            {
                "book_id": 2,
                "user_id": 1,
                "rating": 4,
                "text": "Глубокая психологическая драма. Достоевский мастерски описывает муки совести и метания души Раскольникова.",
                "status_id": 2 # Одобрена
            },
            {
                "book_id": 2,
                "user_id": 3,
                "rating": 3,
                "text": "Отличный роман, но атмосфера слишком давит и угнетает. Читается тяжело.",
                "status_id": 1 # На рассмотрении -> visible in moderator panel
            },
            # Book 3: Дракула (1 approved, 1 rejected)
            {
                "book_id": 3,
                "user_id": 3,
                "rating": 5,
                "text": "Классика готической литературы. Атмосферно, жутко, держит в напряжении до самого конца.",
                "status_id": 2 # Одобрена
            },
            {
                "book_id": 3,
                "user_id": 2,
                "rating": 2,
                "text": "По современным меркам слишком наивно и затянуто. Персонажи плоские и ведут себя нелогично.",
                "status_id": 3 # Отклонена
            }
        ]
        
        for r_dict in reviews_data:
            rev = Review(
                book_id=r_dict["book_id"],
                user_id=r_dict["user_id"],
                rating=r_dict["rating"],
                text=r_dict["text"],
                status_id=r_dict["status_id"]
            )
            db.session.add(rev)
            
        db.session.commit()
        print("Database initialized and seeded with books and reviews successfully!")

if __name__ == "__main__":
    # For running standalone to initialize db
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.root_path, 'library.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    init_db(app)
