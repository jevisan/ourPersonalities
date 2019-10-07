import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SERVER_NAME = os.environ.get('SERVER_NAME') or 'localhost:5000'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'opsupersecretpassword'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    LYRADMIN = ['youremail@example.com']
    MANTADMIN = ['youremail@example.com']
    TWITTER_APP_KEY = os.environ.get('TWITTER_APP_KEY')
    TWITTER_APP_SECRET = os.environ.get('TWITTER_APP_SECRET')
    TWITTER_OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
    TWITTER_OAUTH_TOKEN_SECRET = os.environ.get('TWITTER_OAUTH_TOKEN_SECRET')
