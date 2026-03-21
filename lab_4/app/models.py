from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)
    description = db.Column(db.Text)

    users = db.relationship('User', backref = 'role', lazy = True)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    login = db.Column(db.String(50), nullable = False, unique = True, index = True)
    password_hash = db.Column(db.String(255), nullable = False)
    last_name = db.Column(db.String(50))
    first_name = db.Column(db.String(50), nullable = False)
    middle_name = db.Column(db.String(50))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete = 'SET NULL'), nullable = True)
    created_at = db.Column(db.DateTime, default = datetime.utcnow, server_default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def full_name(self):
        return f"{self.last_name or ''} {self.first_name} {self.middle_name or ''}".strip()
     