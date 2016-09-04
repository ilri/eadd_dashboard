from flask import render_template, redirect, url_for, request, json
from flask_login import login_user, logout_user, login_required
from flask_wtf import Form
from voluptuous import Schema, Required, Invalid, All, Match, Length, Any

from dash import app, db1
from dash.models import User
from dash.pwutils import verify_password

from .login import LoginForm

import sys

last_error = {}

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
    query = """
    select
        location_district as id, location_district as text, "-1" as parentid
    from farmer
    where extension_personnel_id not in(13,2) and project like 'eadd%' and project not like '%test%'
        and location_district is not null and location_district != ""
    group by location_district
    order by project, location_district
    """
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
    form_data = request.get_json()
    farmer_id = int(form_data['farmer_id'])
    # get the farmer id details
    query = """
    select
      a.id as farmer_id, a.name as farmer_name, a.mobile_no, a.mobile_no2, a.location_district as hub, a.hh_id, a.gps_longitude, a.gps_latitude, a.pref_locale as locale, b.name as cf, if(is_active = 1, 'Yes', 'No') as is_active
    from farmer as a inner join extension_personnel as b on a.extension_personnel_id = b.id
    where a.id = %d
    """
    cursor.execute(query % (farmer_id))
    farmer = cursor.fetchone()

    #now get the cows belonging to this farmer
    query = """
    select
      id as cow_id, name as cow_name, ear_tag_number as ear_tag, date_of_birth as dob, sex, breed_group, sire_id, dam_id, milking_status as is_milking, if(in_calf=1,'Yes','No') as is_incalf, parity, if(farmer_id = 0, 0, 1) as is_active
    from cow
    where farmer_id = %d or old_farmer_id = %d
    """
    cursor.execute(query % (farmer_id, farmer_id))
    cows = cursor.fetchall()
    return json.jsonify({'farmer': farmer, 'animals': cows})


@app.route('/edit_farmer', methods=['GET'])
@login_required
def edit_farmer():
    return render_template('farmer_edit.html', form=Form())


@app.route('/autocomplete', methods=['GET'])
@login_required
def autocomplete_options():
    criteria = request.args.get('query')
    option = request.args.get('resource')

    if(option == 'all_cfs'):
        suggestions = all_cfs(criteria)
    elif(option == 'all_locale'):
        suggestions = all_locales(criteria)
    elif(option == 'all_hubs'):
        suggestions = all_hubs(criteria)

    to_return = {'query': criteria, 'suggestions': suggestions}
    return json.jsonify(to_return)


def all_cfs(criteria):
    cursor = db1.cursor()
    query = """
    select id as cf_id, name from extension_personnel where name like '%s' order by name
    """

    cursor.execute(query % ('%' + criteria + '%'))
    cfs = cursor.fetchall()
    suggestions = []
    for cf in cfs:
        suggestions.append({'data': cf['name'], 'value': cf['name']})
    return suggestions


def all_locales(criteria):
    cursor = db1.cursor()
    query = """
    select language from locales where prefix like '%s' or language like '%s' order by language
    """

    cursor.execute(query % ('%' + criteria + '%', '%' + criteria + '%'))
    locales = cursor.fetchall()
    suggestions = []
    for loc in locales:
        suggestions.append({'data': loc['language'], 'value': loc['language']})
    return suggestions


def all_hubs(criteria):
    cursor = db1.cursor()
    query = """
    select location_district as hub from farmer where location_district like '%s' group by location_district order by location_district
    """

    cursor.execute(query % ('%' + criteria + '%'))
    hubs = cursor.fetchall()
    suggestions = []
    for hub in hubs:
        suggestions.append({'data': hub['hub'], 'value': hub['hub']})
    return suggestions


@app.route('/save_farmer', methods=['POST'])
@login_required
def save_farmer():
    form_data = request.get_json()

    print('Validating the passed data for the farmer')
    ret = validate_farmer(form_data)
    if(ret == 1):
        return last_error
    print('Validation passed, now lets save the data')

    print('Normalise the passed data')
    form_data = normalise_farmer(form_data)
    if(form_data == 0):
        return json.jsonify({'error': True, 'msg': 'Error while executing the query'})
    print(form_data)
    print('Normalisation passed')

    # since we have the farmer_id, it means we have a new farmer, so update the farmer
    update_farmer(form_data)
    db1.commit()
    print('Farmer updated.... ')
    return json.jsonify({'error': False, 'msg': 'Farmer updated successfully'})


def normalise_farmer(data):
    cursor = db1.cursor()
    """
    Normalise the data passed from the user, by converting the options to FK, indices etc
    """
    # check that the locale is made up of 2 letters only
    if(len(data['locale']) != 2):
        query = "select prefix from locales where language = '%s'"
        try:
            cursor.execute(query % (data['locale']))
            locale = cursor.fetchone()
        except Exception as e:
            print("\nError while running\n", query, "\nData:\n", data['locale'])
            print(e)
            # last_error = {'error': True, 'msg': e}
            return 0
        data['locale'] = locale['prefix']

    # check that the cf is an integer
    if not data['cf'].isdigit():
        query = "select id from extension_personnel where name = '%s'"
        # data['cf'] = 'Milka'
        try:
            cursor.execute(query % (data['cf']))
            cf = cursor.fetchone()
            print(cf)
        except Exception as e:
            print("\nError while running\n", query, "\nData:\n", data['cf'])
            print(e)
            # last_error = {'error': True, 'msg': 'Error while executing the query'}
            return 0
        data['cf'] = cf['id']

    # normalise whether the farmer is active
    if(data['is_active'].isalpha()):
        data['is_active'] = 1 if data['is_active'] == 'yes' else 0

    return data


def validate_farmer(form_data):
    # define our constraints
    validator = Schema({
        Required('farmer_id'): All(int, msg='Missing farmer id. Stop tampering with the system.'),
        Required('farmer_name'): All(str, Length(min=7, max=20), msg='The farmer name should have 7-20 characters'),
        Required('mobile_no'): All(Match('^25[456]\d{9}$', msg="Mobile should be like '254700123456'")),
        'mobile_no1': Any(Match('^25[456]\d{9}$', msg="Mobile should be like '254700123456'"), ''),
        Required('cf'): All(str, Length(min=7, max=20), msg='The farmer name should have 7-20 characters'),
        Required('hub'): All(str, Length(min=3, max=20), msg='The hub name should have 3-20 characters'),
        Required('locale'): All(str, Length(min=2, max=20), msg='The language should have 2-20 characters'),
        'gps_lat': All(Match('^\-?\d{1}\.\d{3,10}$'), msg='The GPS latitude should be like 0.89877878'),
        'gps_lon': All(Match('^0?\d{2}\.\d{3,10}$'), msg='The GPS latitude should be like 36.89877878'),
        Required('is_active'): All(str, Any('yes', 'no'), msg='Select whether the farmer is active or not')
    })

    # format our data
    data = {
        'farmer_id': int(form_data['farmer_id']),
        'farmer_name': str(form_data['farmer_name']),
        'mobile_no': form_data['mobile_no'],
        'mobile_no1': form_data['mobile_no1'],
        'cf': form_data['cf'],
        'hub': form_data['hub'],
        'locale': form_data['locale'],
        'gps_lat': form_data['gps_lat'],
        'gps_lon': form_data['gps_lon'],
        'is_active': form_data['is_active']
    }
    try:
        validator(data)
    except Invalid as e:
        last_error = json.jsonify({'error': True, 'msg': e.msg})
        return 1
    return 0


def update_farmer(data):
    cursor = db1.cursor()
    query = """
        update farmer set
            name ='%s', mobile_no = '%s', location_district = '%s', gps_longitude = '%s', gps_latitude = '%s',
            extension_personnel_id = %d, pref_locale = '%s', is_active = %d, mobile_no2 = '%s'
        where id = %d
    """
    vals = (data['farmer_name'], data['mobile_no'], data['hub'], data['gps_lon'], data['gps_lat'],
        int(data['cf']), data['locale'], data['is_active'], data['mobile_no1'], int(data['farmer_id']))

    try:
        cursor.execute(query % vals)
    except (AttributeError) as e:
        print("Error occurred while executing:\n", query % "\nVals:\n", vals)
        print(e)
        last_error = json.jsonify({'error': True, 'msg': 'Error while executing the query'})
        return 1

    return 0
