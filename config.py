import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-af'

    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    # DATABASE_URL= postgres://name:password@houst:port/blog_api_db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    #  or \
    #     'sqlite:///' + os.path.join(basedir, 'app.db')
    # 'postgres://localhost/dashboard_flask_db?user=hologit&password=30121994'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['git.bachin@gmail.com']
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
