from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Role
from app.forms import UserForm, EditForm, ChangepasswordForm



bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@bp.route('/login', methods= ['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        user = User.query.filter_by(login= login).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно авторизовались!', 'success')
            redirect(url_for('main.index'))
        else: flash('Неправильный логин или пароль', 'error')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('main.index'))

@bp.route('/user/<int:id>')
def view_user(id):
    user = User.query.get_or_404(id)
    return render_template('view.html', user=user)

@bp.route('/user/create', methods=['GET', 'POST'])
@login_required
def create_user():
    form = UserForm(request.form)
    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles]
    
    if request.method == 'POST' and form.validate():
        try:
            if User.query.filter_by(login=form.login.data).first():
                flash('Логин уже занят', 'error')
                return render_template('user_form.html', form=form, roles=roles, is_edit=False)
            
            user = User(
                login=form.login.data,
                last_name=form.last_name.data or None,
                first_name=form.first_name.data,
                middle_name=form.middle_name.data or None,
                role_id=form.role_id.data or None
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            flash('Пользователь создан', 'success')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка: {str(e)}', 'error')
    
    return render_template('user_form.html', form=form, roles=roles, is_edit=False)

@bp.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = EditForm(request.form, obj=user)
    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles]
    
    if request.method == 'POST' and form.validate():
        try:
            user.last_name = form.last_name.data or None
            user.first_name = form.first_name.data
            user.middle_name = form.middle_name.data or None
            user.role_id = form.role_id.data or None
            
            db.session.commit()
            flash('Данные обновлены', 'success')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка: {str(e)}', 'error')
    
    return render_template('user_form.html', form=form, roles=roles, is_edit=True, user=user)

@bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь удалён', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка удаления: {str(e)}', 'error')
    return redirect(url_for('main.index'))

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangepasswordForm(request.form)
    
    if request.method == 'POST' and form.validate():
        if not current_user.check_password(form.old_password.data):
            flash('Неверный старый пароль', 'error')
            return render_template('change_password.html', form=form)
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Пароль изменён', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('change_password.html', form=form)
