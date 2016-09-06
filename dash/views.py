from flask import render_template, redirect, url_for, request, json
from flask_login import login_user, logout_user, login_required
from flask_wtf import Form
from voluptuous import Schema, Required, Invalid, All, Match, Length, Any

from dash import app, db1
from dash.models import User
from dash.pwutils import verify_password

from .login import LoginForm

import sys

last_error = ''


@app.route('/', methods=['GET', 'POST'])
def show_login():
    loginform = LoginForm()
    if loginform.validate_on_submit():
        username = loginform.username.data
        password = loginform.password.data
        user = User.query.filter_by(username=username).first()
        print(user)

        if user == None:
            return render_template('login.html',
						   title='EADD Ngombe Planner - Dashboard',
                           username_msg='Invalid username',
						   form=loginform)
        if verify_password(password, user.password):
            login_user(user)
        else:
            print("Couldn't authenticate the user... redirect to login page")
            return render_template('login.html',
						   title='EADD Ngombe Planner - Dashboard',
                           addinfo='Invalid username or password',
						   form=loginform)

        next = request.args.get('next')
        return redirect(next or url_for('show_dashboard'))

    return render_template('login.html',
						   title='EADD Ngombe Planner - Dashboard',
						   form=loginform)


@app.route('/logout')
@login_required
def user_logout():
    logout_user()
    return redirect(url_for('show_login'))


@app.route('/dashboard')
@login_required
def show_dashboard():
    cursor = db1.cursor()
    # get all the locations
    query = """
    select
        location_district as id, location_district as text, "-1" as parentid, 1 as is_active
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
        id as id, name as text, location_district as parentid, is_active
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
      id as cow_id, name as cow_name, ear_tag_number as ear_tag, date_of_birth as dob, sex, breed_group, sire_id, dam_id, milking_status as is_milking, if(in_calf=1,'Yes','No') as is_incalf, parity, if(farmer_id = 0, 'No', 'Yes') as is_active
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
    elif(option == 'all_breeds'):
        suggestions = all_breeds(criteria)
    elif(option == 'milking_statuses'):
        suggestions = all_milking_statuses(criteria)
    elif(option == 'global_search'):
        suggestions = global_search(criteria)

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


def all_breeds(criteria):
    cursor = db1.cursor()
    query = """
    select breed_group as breed from cow where breed_group like '%s' group by breed_group order by breed_group
    """

    cursor.execute(query % ('%' + criteria + '%'))
    breeds = cursor.fetchall()
    suggestions = []
    for breed in breeds:
        suggestions.append({'data': breed['breed'], 'value': breed['breed']})
    return suggestions


def all_milking_statuses(criteria):
    cursor = db1.cursor()
    query = """
    select milking_status as milk_status from cow where milking_status like '%s' group by milking_status order by milking_status
    """

    cursor.execute(query % ('%' + criteria + '%'))
    milk_statuses = cursor.fetchall()
    suggestions = []
    for milk_status in milk_statuses:
        suggestions.append({'data': milk_status['milk_status'], 'value': milk_status['milk_status']})
    return suggestions


@app.route('/save_farmer', methods=['POST'])
@login_required
def save_farmer():
    form_data = request.get_json()

    print('Validating the passed data for the farmer')
    ret = validate_farmer(form_data)
    if(ret == 1):
        return json.jsonify({'error': True, 'msg': last_error})

    print('Validation passed, now lets save the data')

    print('Normalise the passed data')
    form_data = normalise_farmer(form_data)
    if(form_data == 0):
        return json.jsonify({'error': True, 'msg': 'Error while executing the query'})
    print(form_data)
    print('Normalisation passed')

    if 'farmer_id' not in form_data:
        # save a new farmer
        ret = save_new_farmer(form_data)
        if(ret == 1):
            return json.jsonify({'error': True, 'msg': last_error})
    else:
        # since we have the farmer_id, it means we have a new farmer, so update the farmer
        ret = update_farmer(form_data)
        if(ret == 1):
            return json.jsonify({'error': True, 'msg': last_error})
    db1.commit()
    print('Farmer saved/updated.... ')
    return json.jsonify({'error': False, 'msg': 'Farmer saved successfully'})


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
            last_error = 'Error while saving farmer'
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
            last_error = 'Error while executing the query'
            return 0
        data['cf'] = cf['id']

    # normalise whether the farmer is active
    if(data['is_active'].isalpha()):
        data['is_active'] = 1 if data['is_active'] == 'yes' else 0

    return data


def validate_farmer(form_data):
    # define our constraints
    validator = Schema({
        Required('csrf_token'): All(str),
        'farmer_id': All(int, msg='Invalid farmer id. Stop tampering with the system.'),
        Required('farmer_name'): All(str, Length(min=7, max=20), msg='The farmer name should have 7-20 characters'),
        Required('mobile_no'): All(Match('^(25[456]|0)\d{9}$', msg="Mobile should be like '254700123456'")),
        'mobile_no1': Any(Match('^(25[456]|0)\d{9}$', msg="Mobile should be like '254700123456'"), ''),
        Required('cf'): All(str, Length(min=7, max=20), msg='The farmer name should have 7-20 characters'),
        Required('hub'): All(str, Length(min=3, max=20), msg='The hub name should have 3-20 characters'),
        Required('locale'): All(str, Length(min=2, max=20), msg='The language should have 2-20 characters'),
        'gps_lat': All(Match('^\-?\d{1}\.\d{3,10}$'), msg='The GPS latitude should be like 0.89877878'),
        'gps_lon': All(Match('^0?\d{2}\.\d{3,10}$'), msg='The GPS latitude should be like 36.89877878'),
        Required('is_active'): All(str, Any('yes', 'no'), msg='Select whether the farmer is active or not')
    })

    # format our data
    if 'farmer_id' in form_data:
        form_data['farmer_id'] = int(form_data['farmer_id'])

    try:
        validator(form_data)
    except Invalid as e:
        print('Error while validating farmer')
        print(e)
        last_error = e.msg
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
        last_error = 'Error while executing the query'
        return 1
    return 0


def save_new_farmer(data):
    cursor = db1.cursor()
    query = """
        insert into
        farmer(name, mobile_no, location_district, gps_latitude, gps_longitude, extension_personnel_id, pref_locale, is_active, mobile_no2)
        values('%s',  '%s', '%s', '%s', '%s', %d, '%s', %d, '%s')
    """
    vals = (data['farmer_name'], data['mobile_no'], data['hub'], data['gps_lon'], data['gps_lat'],
			int(data['cf']), data['locale'], data['is_active'], data['mobile_no1'])

    try:
        cursor.execute(query % vals)
    except (AttributeError) as e:
        print("Error occurred while executing:\n", query % "\nVals:\n", vals)
        print(e)
        last_error = 'Error while executing the query'
        return 1
    return 0


@app.route('/toggle_farmer_status', methods=['POST'])
@login_required
def toggle_farmer_status():
    cursor = db1.cursor()
    data = request.get_json()
    data['is_active'] = 1 if data['is_active'] == 'yes' else 0
    query = 'update farmer set is_active = %d where id = %d'
    vals = (int(data['is_active']), int(data['farmer_id']))
    try:
        cursor.execute(query % vals)
    except (AttributeError) as e:
        print("Error occurred while executing:\n", query % "\nVals:\n", vals)
        print(e)
        return json.jsonify({'error': True, 'msg': 'Error while updating the farmer'})

    db1.commit()
    return json.jsonify({'error': False, 'msg': 'The farmer was updated well'})


@app.route('/toggle_cow_status', methods=['POST'])
@login_required
def toggle_cow_status():
    cursor = db1.cursor()
    data = request.get_json()

    if(data['is_active'] == 'no'):
        query = 'update cow set old_farmer_id = %d, farmer_id = 0 where id = %d'
        vals = (int(data['farmer_id']), int(data['cow_id']))
        try:
            cursor.execute(query % vals)
        except (AttributeError) as e:
            print("Error occurred while executing:\n", query % "\nVals:\n", vals)
            print(e)
            return json.jsonify({'error': True, 'msg': 'Error while updating the cow status'})
    else:
        query = 'update cow set old_farmer_id = NULL, farmer_id = %d where id = %d'
        vals = (int(data['farmer_id']), int(data['cow_id']))
        try:
            cursor.execute(query % vals)
        except (AttributeError) as e:
            print("Error occurred while executing:\n", query % "\nVals:\n", vals)
            print(e)
            return json.jsonify({'error': True, 'msg': 'Error while updating the cow status'})

    db1.commit()
    return json.jsonify({'error': False, 'msg': 'The cow was updated well'})


@app.route('/save_cow', methods=['POST'])
@login_required
def save_cow():
    form_data = request.get_json()

    print('Cow: Validating the passed data')
    ret = validate_cow(form_data)
    if(ret == 1):
        return json.jsonify({'error': True, 'msg': last_error})
    print('Cow: Validation passed, now lets save the data')

    print('Cow: Normalise the passed data')
    form_data = normalise_cow(form_data)
    if(form_data == 1):
        return json.jsonify({'error': True, 'msg': last_error})
    print(form_data)
    print('Normalisation passed')

    # since we have the cow_id, update the cow details
    update_cow(form_data)
    db1.commit()
    print('Cow updated.... ')
    return json.jsonify({'error': False, 'msg': 'Cow updated successfully'})


def validate_cow(form_data):
    # define our constraints
    validator = Schema({
        Required('farmer_id'): All(int, msg='Missing farmer id. Stop tampering with the system.'),
        Required('cow_id'): All(int, msg='Missing cow id. Stop tampering with the system.'),
        Required('cow_name'): All(str, Length(min=3, max=15), msg='The cow name should have 3-15 characters'),
        Required('breed_group'): All(str, Length(min=5, max=15), msg='The breed name should have 5-15 characters'),
        Required('csrf_token'): All(str),
        # 'dam': Any(str, Length(min=3, max=15), msg="The dam name should be between 3-15 characters"),
        # 'sire': Any(str, Length(min=3, max=15), msg="The sire name should be between 3-15 characters"),
        'ear_tag': Any(str, Length(min=3, max=15), msg="The ear tag should be between 3-15 characters"),
        Required('dob'): All(Match('^\d{4}\-\d{2}\-\d{2}$'), msg='Please add the DoB for the cow'),
        'parity': All(int, msg='Please specify the cow parity.'),
        Required('is_active'): All(str, Any('yes', 'no'), msg='Select whether the cow is active or not'),
        Required('sex'): All(str, Any('Male', 'Female'), msg='Specify the sex of the cow'),
        'is_incalf': All(str, Any('yes', 'no'), msg='Select whether the cow is incalf or not'),
        'milking_status': All(str, Any('adult_milking', 'adult_not_milking'), msg='Select the status of the cow')
    })

    form_data['parity'] = int(form_data['parity'])
    print(form_data)
    try:
        validator(form_data)
    except Invalid as e:
        last_error = e.msg
        print(e)
        return 1
    return 0


def normalise_cow(data):
    """
    Normalise the data passed from the user, by converting the options to FK, indices etc
    """
    # ensure that we have parity, milking_status and whether is incalf for the cows
    if(data['sex'] == 'female'):
        if(data['is_incalf'] == ''):
            print('Expecting for all cows to have an incalf status')
            return 1
        data['is_incalf'] = 1 if data['is_incalf'] == 'yes' else 0

        if(data["adult_milking"] == ''):
            print('Expecting for all cows to have a milking status')
            return 1
    return data

def update_cow(data):
    cursor = db1.cursor()
    query = """
        update cow set
            name ='%s', ear_tag_number = '%s', date_of_birth = '%s', sex = '%s', breed_group = '%s',
            milking_status = '%s', in_calf = '%s', parity = %d
        where id = %d
    """
    vals = (data['cow_name'], data['ear_tag'], data['dob'], data['sex'], data['breed_group'],
			data['milking_status'], data['is_incalf'], data['parity'], int(data['cow_id']))

    try:
        cursor.execute(query % vals)
    except (AttributeError) as e:
        print("Error occurred while executing:\n", query % "\nVals:\n", vals)
        print(e)
        last_error = 'Error while executing the query'
        return 1

    # update the farmer_id if there is need
    if(data['is_active'] == 'no'):
        query = 'update cow set old_farmer_id = %d, farmer_id = 0 where id = %d'
        vals = (int(data['farmer_id']), int(data['cow_id']))
        try:
            cursor.execute(query % vals)
        except (AttributeError) as e:
            print("Error occurred while executing:\n", query % "\nVals:\n", vals)
            print(e)
            last_error = 'Error while executing the query'
            return 1
    return 0


def global_search(criteria):
    cursor = db1.cursor()
    # search from the farmers table
    query = """
    select id, name, hh_id, location_district as hub, mobile_no, mobile_no2
    from farmer
    where name like '%s' or hh_id like '%s' or location_district like '%s' or mobile_no like '%s' or mobile_no2 like '%s'
    order by name
    """
    cr = '%' + criteria + '%'
    vals = (cr, cr, cr, cr, cr)
    try:
        cursor.execute(query % vals)
    except (AttributeError) as e:
        print("Error occurred while executing:\n", query % "\nVals:\n", vals)
        print(e)
        return json.jsonify({'error': True, 'msg': 'There was an error while fetching data from the database'})
    farmers = cursor.fetchall()

    suggestions = []
    for f in farmers:
        f['hhid1'] = '' if f['hh_id'] is None else f['hh_id']
        f['mobile2'] = '' if f['mobile_no2'] is None else f['mobile_no2']
        value = "Farmer: %(name)s %(hub)s %(hhid1)s %(mobile_no)s %(mobile2)s" % f

        data = {'category': 'Farmer', 'id': f['id'], 'search': 'global'}
        suggestions.append({'value': value, 'data': data})

    # search from the cows table
    query = """
    select id, farmer_id, old_farmer_id, name, ear_tag_number as ear_tag
    from cow
    where name like '%s' or ear_tag_number like '%s'
    order by name
    """
    cr = '%' + criteria + '%'
    vals = (cr, cr)
    try:
        cursor.execute(query % vals)
    except (AttributeError) as e:
        print("Error occurred while executing:\n", query % "\nVals:\n", vals)
        print(e)
        return json.jsonify({'error': True, 'msg': 'There was an error while fetching data from the database'})
    cows = cursor.fetchall()

    for c in cows:
        c['ear_tag1'] = '' if c['ear_tag'] is None else c['ear_tag']
        c['farmer_id'] = c['old_farmer_id'] if c['farmer_id'] == 0 else c['farmer_id']
        value = "Cow: %(name)s %(ear_tag1)s" % c
        data = {'category': 'Cow', 'id': c['id'], 'search': 'global', 'farmer_id': c['farmer_id']}
        suggestions.append({'value': value, 'data': data})

    # search from the cfs table
    query = """
    select id, name, mobile_no
    from extension_personnel
    where name like '%s' or mobile_no like '%s'
    order by name
    """
    cr = '%' + criteria + '%'
    vals = (cr, cr)
    try:
        cursor.execute(query % vals)
    except (AttributeError) as e:
        print("Error occurred while executing:\n", query % "\nVals:\n", vals)
        print(e)
        return json.jsonify({'error': True, 'msg': 'There was an error while fetching data from the database'})
    cfs = cursor.fetchall()

    for c in cfs:
        value = "CF: %(name)s %(mobile_no)s" % c
        data = {'category': 'CF', 'id': c['id'], 'search': 'global'}
        suggestions.append({'value': value, 'data': data})

    return suggestions


@app.route('/add_new_template', methods=['POST'])
@login_required
def add_new_templates():
    template = render_template('add_new_template.html', form=Form())
    return json.jsonify({'error': False, 'template': template})

@app.route('/edit_template', methods=['POST'])
@login_required
def edit_template():
    template = render_template('farmer_edit.html', form=Form())
    return json.jsonify({'error': False, 'template': template})

@app.route('/cow_stats')
@login_required
def cow_stats():
    return render_template('pending.html')


@app.route('/farmer_stats')
@login_required
def farmer_stats():
    return render_template('pending.html')


@app.route('/canned_queries')
@login_required
def canned_queries():
    return render_template('pending.html')