from flask import Flask, request
from flask_login import LoginManager, current_user
from config import Config
from app.models import db, User, Role, Visit_logs

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

    from app.reports import bp_reports
    app.register_blueprint(bp_reports)

    @app.before_request
    def log_visit():
        if request.endpoint and 'static' not in request.endpoint:
            try:
                log_entry = Visit_logs(
                    path=request.path,
                    user_id=current_user.id if current_user.is_authenticated else None
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception:
                db.session.rollback()

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


