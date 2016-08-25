import MySQLdb
import MySQLdb.cursors
from flask_sqlalchemy import SQLAlchemy

from flask import Flask
from flask_login import LoginManager

# Define the app object and load the config from file
app = Flask(__name__, static_folder='static')

# Read database settings from the configuration file
app.config.from_object('config')
dbhost = app.config['DBHOST']
dbname = app.config['DBNAME']
dbuser = app.config['DBUSERNAME']
dbpass = app.config['DBPASSWORD']
dbport = app.config['DBPORT']

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://%s:%s@%s/%s' % (app.config['DBUSERNAME'], app.config['DBPASSWORD'], app.config['DBHOST'], app.config['DBNAME'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
db1 = MySQLdb.connect(host = dbhost, port = dbport, user = dbuser, passwd = dbpass, db = dbname, cursorclass=MySQLdb.cursors.DictCursor)

login_manager = LoginManager(app)

# from dash import views
from dash import models, views