import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect

# Define the app object and load the config from file
csrf = CsrfProtect()
app = Flask(__name__, static_folder='static')
csrf.init_app(app)

# Read database settings from the configuration file
app.config.from_object('config')

if os.environ.get('DATABASE_URL') is None:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://%s:%s@%s/%s' % (app.config['DBUSERNAME'], app.config['DBPASSWORD'], app.config['DBHOST'], app.config['DBNAME'])
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

login_manager = LoginManager(app)

# from dash import views
from dash import models, views