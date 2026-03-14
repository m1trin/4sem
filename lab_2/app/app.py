from flask import Flask, render_template, request, make_response, url_for
import re

app = Flask(__name__)

def is_mobile_number(phone):
    if not re.match(r'^[\d\s\(\)\.\-\+]+$', phone):
        return False, 'Недопустимый ввод. В номере телефона встречаются недопустимые символы', None
    
    digits = re.sub(r'\D', '', phone)
    
    if phone.startswith('+7') or phone.startswith('8'):
        if len(digits) != 11:
            return False, 'Недопустимый ввод. Неверное количество цифр', None
    elif len(digits) != 10:
        return False, 'Недопустимый ввод. Неверное количество цифр', None

    last_10 = digits[-10:]
    formatted = f'8-{last_10[:3]}-{last_10[3:6]}-{last_10[6:8]}-{last_10[8:10]}'
    return True, None, formatted

@app.route('/')
def index():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    
    if username:
        return render_template('index.html', 
                               title='Авторизация',
                               username=username,
                               password=password,
                               logged_in=True)
    return render_template('index.html', title='Авторизация')

@app.route('/login.html', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    resp = make_response(render_template('index.html', 
                                         title='Авторизация',
                                         username=username,
                                         password=password,
                                         logged_in=True))
    
    if username:
        resp.set_cookie('username', username, max_age=3600)
    if password:
        resp.set_cookie('password', password, max_age=3600)
        
    return resp

@app.route('/cookie.html')    
def cookie():
    return render_template('cookie.html', title='Cookie')

@app.route('/form.html')
def form():
    username = request.cookies.get('username', '')
    password = request.cookies.get('password', '')
    
    form_data = {
        'Имя': username or 'Нет данных',
        'Email': f"{username}@example.com" if username else 'Нет данных',
        'Пароль': password or 'Нет данных'
    }
    
    return render_template('form.html', title='Данные формы', form=form_data)

@app.route('/headers.html')
def headers():
    return render_template('headers.html', title='Заголовки запроса')

@app.route('/url.html')
def url():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    
    url_params = {}
    if username:
        url_params['username'] = username
    if password:
        url_params['password'] = password
    
    current_url = None
    if username:
        current_url = f"?username={username}" + (f"&password={password}" if password else "")
    
    return render_template('url.html', 
                           title='Параметры URL', 
                           url=url_params,
                           current_url=current_url)

@app.route('/mobile_number.html', methods=['GET', 'POST'])
def mobile_number():
    error = None
    f_phone = None

    if request.method == 'POST':
        phone = request.form.get('phone', '')
        valid, er_msg, formatted = is_mobile_number(phone)

        if valid:
            f_phone = formatted
        else:
            error = er_msg

    return render_template('mobile_number.html', 
                           title='Проверка номера телефона',
                           error=error, 
                           f_phone=f_phone)

if __name__ == '__main__':
    app.run(debug=True)