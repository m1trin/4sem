from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin


app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа необходимо пройти аунтификацию'
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

users = {'user': User('1', 'user', 'qwerty')}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if user.id == user_id:
            return user
    return None

def safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route('/')
def index():
    return render_template('index.html', title = 'Главная страница')

@app.route('/counter')
def counter():
    count = session.get('visit_count', 0) + 1
    session['visit_count'] = count
    return render_template('counter.html', title = 'Счетчик посещений', count = count)

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')

        user = users.get(username) 
        if user and user.password == password:
            login_user(user, remember= bool(remember))
            flash('Вы вошли в систему!', 'success')

            next_page = request.args.get('next')
            if next_page and safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Неправильный логин или пароль', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', title = 'Авторизация')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

@app.route('/secret')
@login_required
def secret():
    flash('Страница только для авторизованных пользователей')
    return render_template('secret.html', title = 'Секретная страница')

if __name__ == '__main__':
    app.run(debug=True)



