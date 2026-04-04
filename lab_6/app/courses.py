from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, asc
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

RATING_CHOICES = [
    (5, 'отлично'),
    (4, 'хорошо'),
    (3, 'удовлетворительно'),
    (2, 'неудовлетворительно'),
    (1, 'плохо'),
    (0, 'ужасно'),
]

SORT_CHOICES = {
    'newest': ('По новизне', desc(Review.created_at)),
    'positive_first': ('Сначала положительные', desc(Review.rating)),
    'negative_first': ('Сначала отрицательные', asc(Review.rating)),
}

def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())

@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)

@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html',
                            categories=categories,
                            users=users,
                            course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')

    return redirect(url_for('courses.index'))

@bp.route('/<int:course_id>')
def show(course_id):
    course = db.get_or_404(Course, course_id)
    
    RATING_CHOICES = [
        (5, 'отлично'),
        (4, 'хорошо'),
        (3, 'удовлетворительно'),
        (2, 'неудовлетворительно'),
        (1, 'плохо'),
        (0, 'ужасно'),
    ]
    
    return render_template('courses/show.html', 
                          course=course,
                          rating_choices=RATING_CHOICES)

@bp.route('/<int:course_id>/reviews')
def reviews(course_id):
    course = db.get_or_404(Course, course_id)
    
    sort = request.args.get('sort', 'newest')
    sort_direction = SORT_CHOICES.get(sort, SORT_CHOICES['newest'])[1]
    
    reviews_query = db.select(Review).filter_by(course_id=course_id).order_by(sort_direction)
    pagination = db.paginate(reviews_query, per_page=10)
    reviews_list = pagination.items
    
    user_review = None
    if current_user.is_authenticated:
        user_review = db.session.execute(
            db.select(Review).filter_by(course_id=course_id, user_id=current_user.id)
        ).scalar()
    
    return render_template(
        'courses/reviews.html',
        course=course,
        reviews=reviews_list,
        pagination=pagination,
        sort=sort,
        sort_choices=SORT_CHOICES,
        rating_choices=RATING_CHOICES,
        user_review=user_review
    )


@bp.route('/<int:course_id>/reviews/create', methods=['POST'])
@login_required
def create_review(course_id):
    course = db.get_or_404(Course, course_id)
    
    # Проверяем, не оставлял ли пользователь уже отзыв
    existing_review = db.session.execute(
        db.select(Review).filter_by(course_id=course_id, user_id=current_user.id)
    ).scalar()
    
    if existing_review:
        flash('Вы уже оставляли отзыв на этот курс.', 'warning')
        return redirect(url_for('courses.show', course_id=course_id))
    
    rating = request.form.get('rating', type=int)
    text = request.form.get('text', '').strip()
    
    if rating is None or rating not in [r[0] for r in RATING_CHOICES]:
        flash('Пожалуйста, выберите корректную оценку.', 'danger')
        return redirect(url_for('courses.show', course_id=course_id))
    
    if not text:
        flash('Пожалуйста, введите текст отзыва.', 'danger')
        return redirect(url_for('courses.show', course_id=course_id))
    
    try:

        review = Review(
            rating=rating,
            text=text,
            course_id=course_id,
            user_id=current_user.id
        )
        db.session.add(review)
        
        
        course.rating_sum += rating
        course.rating_num += 1
        
        db.session.commit()
        flash('Ваш отзыв успешно добавлен!', 'success')
        
    except Exception as err:
        db.session.rollback()
        flash(f'Ошибка при сохранении отзыва: {err}', 'danger')
    
    next_page = request.form.get('next', url_for('courses.show', course_id=course_id))
    return redirect(next_page)


@bp.route('/<int:course_id>/reviews/<int:review_id>/edit', methods=['POST'])
@login_required
def edit_review(course_id, review_id):
    review = db.get_or_404(Review, review_id)
    
    if review.user_id != current_user.id:
        flash('Вы можете редактировать только свои отзывы.', 'danger')
        return redirect(url_for('courses.show', course_id=course_id))
    
    old_rating = review.rating
    new_rating = request.form.get('rating', type=int)
    new_text = request.form.get('text', '').strip()
    
    if new_rating is None or new_rating not in [r[0] for r in RATING_CHOICES]:
        flash('Пожалуйста, выберите корректную оценку.', 'danger')
        return redirect(url_for('courses.show', course_id=course_id))
    
    if not new_text:
        flash('Пожалуйста, введите текст отзыва.', 'danger')
        return redirect(url_for('courses.show', course_id=course_id))
    
    try:
        course = db.get_or_404(Course, course_id)
        course.rating_sum = course.rating_sum - old_rating + new_rating
        
        review.rating = new_rating
        review.text = new_text
        
        db.session.commit()
        flash('Ваш отзыв успешно обновлён!', 'success')
        
    except Exception as err:
        db.session.rollback()
        flash(f'Ошибка при обновлении отзыва: {err}', 'danger')
    
    next_page = request.form.get('next', url_for('courses.show', course_id=course_id))
    return redirect(next_page)