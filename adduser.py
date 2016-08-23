#!flask/bin/python
from dash import app, db, models
from dash.pwutils import hash_password

# Create all tables based on classes in models
db.create_all()

# Create default admin user and insert data into the database
admin_user = models.User('admin', hash_password('admin'))
db.session.add(admin_user)
db.session.commit();
