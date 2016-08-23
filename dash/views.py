from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import current_user, login_user, logout_user, login_required
from .login import LoginForm

from dash import app, db
from dash.models import User
from dash.pwutils import hash_password, verify_password

@app.route('/')
@app.route('/index')
def show_index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def show_login():
    loginform = LoginForm()
    if loginform.validate_on_submit():
        username = loginform.username.data
        password = loginform.password.data
        user = User.query.filter_by(username=username).first()

        if verify_password(password, user.password):
            login_user(user)

        next = request.args.get('next')
        return redirect(next or url_for('show_dashboard'))

    return render_template('login.html',
                           title='EADD Ngombe Planner - Dashboard',
                           form=loginform)


@app.route('/logout')
@login_required
def user_logout():
    logout_user()
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def show_dashboard():
    return render_template('home.html')


