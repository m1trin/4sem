from flask import Flask
from flask_login import LoginManager
from config import Config
from app.models import db, User, Role

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Для входа требуется ауентификация'

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        if not Role.query.first():
            admin_role = Role(name= 'Администратор', description = 'Полный доступ')
            user_role = Role(name= 'Пользователь', description = 'Ограниченный доступ')
            db.session.add_all([admin_role, user_role])
            db.session.commit()
        if not User.query.filter_by(login= 'admin').first():
            admin_role = Role.query.filter_by(name= 'Администратор').first()

            admin = User(
                login='admin',
                first_name='Админ',
                last_name='Администратор',
                role_id= admin_role.id
            )

            admin.set_password('Admin123!')
        
            db.session.add(admin)
            db.session.commit()
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


