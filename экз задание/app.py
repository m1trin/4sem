import os
import hashlib
import bleach
import markdown
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import event
from sqlalchemy.engine import Engine

from models import db, Book, Genre, Cover, Role, User, ReviewStatus, Review
from database import init_db

# Enforce foreign key constraints in SQLite for ON DELETE CASCADE
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-electronic-library-ais'

# Set database path to workspace root
db_filename = 'library.db'
db_url = os.environ.get('DATABASE_URL')
if db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.root_path, db_filename)}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cover upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'covers')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Limit upload to 5MB

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для выполнения данного действия необходимо пройти процедуру аутентификации'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Custom Jinja filter for Markdown rendering
@app.template_filter('markdown')
def render_markdown_filter(text):
    return markdown.markdown(text or '')

# Safe tag set for bleach sanitization (permits simple styling but blocks execution)
SAFE_TAGS = [
    'p', 'br', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'
]
SAFE_ATTRIBUTES = {
    'a': ['href', 'title']
}

# Role-based permission decorator
def permission_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Для выполнения данного действия необходимо пройти процедуру аутентификации', 'warning')
                return redirect(url_for('login', next=request.path))
            if current_user.role.name not in roles:
                flash('У вас недостаточно прав для выполнения данного действия', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Database auto-init on startup
db.init_app(app)
with app.app_context():
    db_file_path = os.path.join(app.root_path, db_filename)
    if not os.path.exists(db_file_path):
        init_db(app)

# ----------------- ROUTES -----------------

@app.route('/')
@app.route('/books')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Book.query.order_by(Book.year.desc()).paginate(page=page, per_page=10, error_out=False)
    books = pagination.items
    return render_template('index.html', books=books, pagination=pagination)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        login_val = request.form.get('login')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(login=login_val).first()
        if user:
            from werkzeug.security import check_password_hash
            if check_password_hash(user.password_hash, password):
                login_user(user, remember=remember)
                flash('Вы успешно вошли в систему.', 'success')
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('index'))
                
        flash('Невозможно аутентифицироваться с указанными логином и паролем.', 'danger')
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/books/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()
    return render_template('book_detail.html', book=book, user_review=user_review)

@app.route('/books/new', methods=['GET', 'POST'])
@login_required
@permission_required('Администратор')
def new_book():
    genres_list = Genre.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        short_description = request.form.get('short_description')
        year = request.form.get('year')
        publisher = request.form.get('publisher')
        author = request.form.get('author')
        page_count = request.form.get('page_count')
        genre_ids = request.form.getlist('genres')
        cover_file = request.files.get('cover')
        
        # Validation checks
        if not (title and short_description and year and publisher and author and page_count and genre_ids and cover_file):
            flash('При сохранении данных возникла ошибка. Все поля со звездочкой обязательны.', 'danger')
            return render_template('book_form.html', genres_list=genres_list, is_edit=False)
            
        try:
            # Clean description before saving
            clean_desc = bleach.clean(short_description, tags=SAFE_TAGS, attributes=SAFE_ATTRIBUTES)
            
            # Create Book instance
            book = Book(
                title=title,
                short_description=clean_desc,
                year=int(year),
                publisher=publisher,
                author=author,
                page_count=int(page_count)
            )
            
            # Associate genres
            for g_id in genre_ids:
                genre = Genre.query.get(int(g_id))
                if genre:
                    book.genres.append(genre)
                    
            db.session.add(book)
            db.session.flush()  # Generate book.id for foreign key
            
            # Cover processing with MD5 hash
            file_bytes = cover_file.read()
            md5_hash = hashlib.md5(file_bytes).hexdigest()
            cover_file.seek(0)
            
            existing_cover = Cover.query.filter_by(md5_hash=md5_hash).first()
            if existing_cover:
                # Deduplication: reuse the existing cover file name
                cover = Cover(
                    file_name=existing_cover.file_name,
                    mime_type=cover_file.mimetype or existing_cover.mime_type,
                    md5_hash=md5_hash,
                    book_id=book.id
                )
                db.session.add(cover)
                db.session.commit()
            else:
                # Save as new cover record, then write file on success
                _, ext = os.path.splitext(cover_file.filename)
                ext = ext.lower() if ext else '.jpg'
                
                cover = Cover(
                    file_name="temp",
                    mime_type=cover_file.mimetype or 'image/jpeg',
                    md5_hash=md5_hash,
                    book_id=book.id
                )
                db.session.add(cover)
                db.session.flush()  # Generate cover.id
                
                # Update file name to use cover record ID
                new_file_name = f"{cover.id}{ext}"
                cover.file_name = new_file_name
                db.session.commit()
                
                # Write to filesystem only after successful DB save
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as f:
                    f.write(file_bytes)
                    
            flash('Книга успешно добавлена!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'При сохранении данных возникла ошибка: {str(e)}', 'danger')
            
    return render_template('book_form.html', genres_list=genres_list, is_edit=False)

@app.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('Администратор', 'Модератор')
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    genres_list = Genre.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        short_description = request.form.get('short_description')
        year = request.form.get('year')
        publisher = request.form.get('publisher')
        author = request.form.get('author')
        page_count = request.form.get('page_count')
        genre_ids = request.form.getlist('genres')
        
        if not (title and short_description and year and publisher and author and page_count and genre_ids):
            flash('При сохранении данных возникла ошибка. Все поля со звездочкой обязательны.', 'danger')
            return render_template('book_form.html', book=book, genres_list=genres_list, is_edit=True)
            
        try:
            # Clean description before saving
            clean_desc = bleach.clean(short_description, tags=SAFE_TAGS, attributes=SAFE_ATTRIBUTES)
            
            book.title = title
            book.short_description = clean_desc
            book.year = int(year)
            book.publisher = publisher
            book.author = author
            book.page_count = int(page_count)
            
            # Re-associate genres
            book.genres.clear()
            for g_id in genre_ids:
                genre = Genre.query.get(int(g_id))
                if genre:
                    book.genres.append(genre)
                    
            db.session.commit()
            flash('Книга успешно обновлена!', 'success')
            return redirect(url_for('book_detail', book_id=book.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'При сохранении данных возникла ошибка: {str(e)}', 'danger')
            
    return render_template('book_form.html', book=book, genres_list=genres_list, is_edit=True)

@app.route('/books/<int:book_id>/delete')
@login_required
@permission_required('Администратор')
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        # Check files referenced by covers to clean from filesystem
        for cover in book.covers:
            shared_count = Cover.query.filter(Cover.file_name == cover.file_name, Cover.id != cover.id).count()
            if shared_count == 0:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], cover.file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
        db.session.delete(book)
        db.session.commit()
        flash(f'Книга «{book.title}» и связанные с ней рецензии и обложка успешно удалены!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении книги: {str(e)}', 'danger')
        
    return redirect(url_for('index'))

@app.route('/books/<int:book_id>/review', methods=['POST'])
@login_required
@permission_required('Пользователь', 'Модератор', 'Администратор')
def add_review(book_id):
    book = Book.query.get_or_404(book_id)
    rating = request.form.get('rating')
    text = request.form.get('text')
    
    if not (rating and text):
        flash('Все поля обязательны для заполнения.', 'danger')
        return redirect(url_for('book_detail', book_id=book.id))
        
    # Double check if user has already submitted a review
    existing_review = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()
    if existing_review:
        flash('Вы уже оставили рецензию для этой книги.', 'warning')
        return redirect(url_for('book_detail', book_id=book.id))
        
    try:
        # Sanitize text
        clean_text = bleach.clean(text, tags=SAFE_TAGS, attributes=SAFE_ATTRIBUTES)
        
        review = Review(
            book_id=book.id,
            user_id=current_user.id,
            rating=int(rating),
            text=clean_text,
            status_id=1  # 1 is "На рассмотрении"
        )
        db.session.add(review)
        db.session.commit()
        flash('Рецензия успешно добавлена и отправлена на модерацию!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка сохранения рецензии: {str(e)}', 'danger')
        
    return redirect(url_for('book_detail', book_id=book.id))

@app.route('/my_reviews')
@login_required
@permission_required('Пользователь')
def my_reviews():
    reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.date_added.desc()).all()
    return render_template('my_reviews.html', reviews=reviews)

@app.route('/moderation')
@login_required
@permission_required('Модератор')
def moderation():
    page = request.args.get('page', 1, type=int)
    # Filter for reviews under status "На рассмотрении" (status_id = 1), sorted from oldest to newest (date_added ASC)
    pagination = Review.query.filter_by(status_id=1).order_by(Review.date_added.asc()).paginate(page=page, per_page=10, error_out=False)
    reviews = pagination.items
    return render_template('moderation.html', reviews=reviews, pagination=pagination)

@app.route('/reviews/<int:review_id>/moderate', methods=['GET', 'POST'])
@login_required
@permission_required('Модератор')
def moderate_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            review.status_id = 2  # 2 is "Одобрена"
            flash('Рецензия успешно одобрена!', 'success')
        elif action == 'reject':
            review.status_id = 3  # 3 is "Отклонена"
            flash('Рецензия успешно отклонена.', 'warning')
            
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка изменения статуса рецензии: {str(e)}', 'danger')
            
        return redirect(url_for('moderation'))
        
    return render_template('review_detail.html', review=review)

if __name__ == '__main__':
    # Create upload directory if it does not exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='localhost', port=9500)

