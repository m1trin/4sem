from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def check_rights(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Для доступа нужна аунтификация', 'error')
                return redirect(url_for('main.login'))

            if current_user.role and current_user.role.name in  allowed_roles:
                return f(*args, **kwargs)
            
            flash('У вас недостаточно прав для доступа к данной странице.', 'error')
            
            return redirect(url_for('main.index'))
        return wrapper
    return decorator 
