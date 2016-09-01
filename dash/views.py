from flask import render_template, redirect, url_for, request, json
from flask_login import login_user, logout_user, login_required

from dash import app, db1
from dash.models import User
from dash.pwutils import verify_password

from .login import LoginForm


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
    cursor = db1.cursor()
    # get all the locations
    q1 = """
    select
        location_district as id, location_district as text, "-1" as parentid
    from farmer
    where extension_personnel_id not in(13,2) and project like '%s' and project not like "%s"
        and location_district is not null and location_district != ""
    group by location_district
    order by project, location_district
    """
    query = q1 % ('eadd%', '%test%')
    cursor.execute(query)
    res = cursor.fetchall()

    # get all the farmers
    q2 = """
    select
        id as id, name as text, location_district as parentid
    from farmer
    where location_district is not null and location_district != "" and project not like "%test%"
        and extension_personnel_id not in (13,2)  and project like "eadd%"
    order by name
    """
    cursor.execute(q2)
    res1 = cursor.fetchall()
    res = res + res1

    return render_template('home.html', allfarmers=json.dumps(res))


@app.route('/farmer_details', methods=['POST'])
@login_required
def farmer_details():
    cursor = db1.cursor()
    # get the farmer id details
    query = """
    select
      a.name as farmer_name, a.mobile_no, a.mobile_no2, a.location_district, a.hh_id, a.gps_longitude, a.gps_latitude, a.pref_locale as locale, b.name as cf
    from farmer as a inner join extension_personnel as b on a.extension_personnel_id = b.id
    where a.id = %d
    """
    cursor.execute(query % (request.form['farmer_id']))
    farmer = cursor.fetchone()
    return json.dumps(farmer)


@app.route('/edit_farmer', methods=['GET'])
@login_required
def edit_farmer():
   return render_template('farmer_edit.html')