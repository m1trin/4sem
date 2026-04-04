import os

class Config:
    SECRET_KEY = '123456789'
    db_user = 'postgres'
    db_password = '123'
    db_host = 'localhost'
    db_port = '5432'
    db_name = 'web_users'

    SQLALCHEMY_DATABASE_URI = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
