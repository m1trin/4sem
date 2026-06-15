from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Association table for book-genre (many-to-many)
book_genre = db.Table('book_genre',
    db.Column('book_id', db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    short_description = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)  # year format
    publisher = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    page_count = db.Column(db.Integer, nullable=False)
    
    # Relationships
    genres = db.relationship('Genre', secondary=book_genre, backref=db.backref('books', lazy='dynamic'))
    covers = db.relationship('Cover', backref='book', cascade='all, delete-orphan', passive_deletes=True)
    reviews = db.relationship('Review', backref='book', cascade='all, delete-orphan', passive_deletes=True)

    @property
    def rating_info(self):
        # Only count approved reviews (status_id = 2 is "Одобрена")
        approved_reviews = [r for r in self.reviews if r.status_id == 2]
        count = len(approved_reviews)
        if count == 0:
            return 0.0, 0
        avg = sum(r.rating for r in approved_reviews) / count
        return round(avg, 2), count

class Genre(db.Model):
    __tablename__ = 'genres'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)

class Cover(db.Model):
    __tablename__ = 'covers'
    
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(255), nullable=False)
    md5_hash = db.Column(db.String(255), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    middle_name = db.Column(db.String(255), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    
    role = db.relationship('Role', backref='users')
    reviews = db.relationship('Review', backref='user')

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

    def is_admin(self):
        return self.role.name == 'Администратор'

    def is_moderator(self):
        return self.role.name == 'Модератор'

    def is_user(self):
        return self.role.name == 'Пользователь'

class ReviewStatus(db.Model):
    __tablename__ = 'review_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status_id = db.Column(db.Integer, db.ForeignKey('review_statuses.id'), nullable=False)
    
    status = db.relationship('ReviewStatus', backref='reviews')
