import re
from wtforms import Form, StringField, PasswordField, SelectField, validators

class UserForm(Form):
        login = StringField('Логин',[
                validators.InputRequired(message = 'Поле не должно быть пустым'),
                validators.Regexp('^[0-9a-zA-Z]+$',
                message = 'Только цифры и латинские или кириллические буквы'),
                validators.length(min=5, message = 'Минимум 5 символов')
        ])
        password = PasswordField('Пароль', [
                validators.InputRequired(message='Это поле не должно быть пустым'),
                validators.Length(min=8, max=128, message = 'Минимум 8 символов')
        ])

        last_name = StringField('Фамилия')

        first_name = StringField('Имя', [
                validators.InputRequired(message='Это поле не может быть пустым')
        ])

        middle_name = StringField('Отчество')

        role_id = SelectField('Роль', coerce=int, choices=[])

        def validate_password(self, field):
                
                password = field.data
                
                if not re.search(r'[A-ZА-Я]', password):
                        raise validators.ValidationError('Требуется заглавная буква')
                if not re.search(r'[a-zа-я]', password):
                        raise validators.ValidationError('Требуется строчная буква')
                if not re.search(r'\d', password):
                        raise validators.ValidationError('Требуется цифра')
                if ' ' in password:
                        raise validators.ValidationError('В пароле не должны быть пробелы')
                
                allowed = re.compile(r'^[a-zA-Zа-яА-Я0-9~!?@#$%^&*_\-\+\(\)\[\]\{\}><\/\\|\"\'.,:;]+$')

                if not allowed.match(password):
                        raise validators.ValidationError('Недопустимые символы')
                
class EditForm(UserForm):
        
        login = None
        password = None

class ChangepasswordForm(Form):
        
        old_password = PasswordField('Старый пароль', [
                validators.InputRequired(message= 'Введите старый пароль')
        ])

        new_password = PasswordField('Новый пароль', [
                validators.InputRequired(message='Введите новый пароль'),
                validators.Length(min=8, max=128)
        ])

        confirm_password = PasswordField('Повторите пароль', [
                validators.InputRequired(message='Подтвердите пароль'),
                validators.EqualTo('new_password', 'Пароли не совпадают')
        ])

        def validate_new_password(self, field):
                
                password = field.data
                
                if not re.search(r'[A-ZА-Я]', password):
                        raise validators.ValidationError('Требуется заглавная буква')
                if not re.search(r'[a-zа-я]', password):
                        raise validators.ValidationError('Требуется строчная буква')
                if not re.search(r'\d', password):
                        raise validators.ValidationError('Требуется цифра')
                if ' ' in password:
                        raise validators.ValidationError('В пароле не должны быть пробелы')
                
                allowed = re.compile(r'^[a-zA-Zа-яА-Я0-9~!?@#$%^&*_\-\+\(\)\[\]\{\}><\/\\|\"\'.,:;]+$')

                if not allowed.match(password):
                        raise validators.ValidationError('Недопустимые символы')