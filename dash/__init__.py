from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Define the app object and load the config from file
app = Flask(__name__)
app.config.from_object('config')

# Read database settings from the configuration file
dbhost = app.config['DBHOST']
dbname = app.config['DBNAME']
dbuser = app.config['DBUSERNAME']
dbpass = app.config['DBPASSWORD']

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://%s:%s@%s/%s' % (dbuser, dbpass, dbhost, dbname)
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# from dash import views
from dash import models, views