import os
import json
basedir = os.path.abspath(os.path.dirname(__file__))

with open('config.json') as config_file:
    config = json.load(config_file)

class Config(object):
    SECRET_KEY = config.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 25
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL= True
    MAIL_USERNAME = config.get('GMAIL')
    MAIL_PASSWORD = config.get('PASSWORD')
    ADMINS = ['cmpe165app@gmail.com']
    GOOGLEMAPS_KEY = config.get('GMAPS_API')
    GMAPS_API = config.get('GMAPS_API')
    ROOMS_PER_PAGE = 10
    STRIPE_SECRET_KEY = config.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = config.get('STRIPE_WEBHOOK_SECRET')