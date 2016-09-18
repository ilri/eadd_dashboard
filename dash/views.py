from flask import render_template, redirect, url_for, request, json
from flask_login import login_user, logout_user, login_required
from flask_wtf import Form
from flask import send_file

from dash import app
from dash.models import User
from dash.pwutils import verify_password

from .login import LoginForm
from .queries import Queries
import subprocess
import csv

last_error = ''

@app.route('/', methods=['GET', 'POST'])
def show_login():
    loginform = LoginForm()
    if loginform.validate_on_submit():
        username = loginform.username.data
        password = loginform.password.data
        user = User.query.filter_by(username=username).first()
        # print(user)

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
    # get all the data to be used to construct the tree
    tree_data = Queries.farmer_tree_data()
    return render_template('home.html', allfarmers=json.dumps(tree_data))


@app.route('/farmer_details', methods=['POST'])
@login_required
def farmer_details():
    form_data = request.get_json()
    farmer_id = int(form_data['farmer_id'])
    details = Queries.farmer_details(farmer_id)

    return json.jsonify(details)


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
        suggestions = Queries.all_cfs(criteria)
    elif(option == 'all_locale'):
        suggestions = Queries.all_locales(criteria)
    elif(option == 'all_hubs'):
        suggestions = Queries.all_hubs(criteria)
    elif(option == 'all_breeds'):
        suggestions = Queries.all_breeds(criteria)
    elif(option == 'milking_statuses'):
        suggestions = Queries.all_milking_statuses(criteria)
    elif(option == 'global_search'):
        suggestions = Queries.global_search(criteria)
    elif(option == 'farmer'):
        suggestions = Queries.all_farmers(criteria)

    to_return = {'query': criteria, 'suggestions': suggestions}
    return json.jsonify(to_return)


@app.route('/save_farmer', methods=['POST'])
@login_required
def save_farmer():
    form_data = request.get_json()

    print('Validating the passed data for the farmer')
    ret = Queries.validate_farmer(form_data)
    if(ret == 1):
        return json.jsonify({'error': True, 'msg': last_error})

    print('Validation passed, now lets save the data')

    print('Normalise the passed data')
    form_data = Queries.normalise_farmer(form_data)
    if(form_data == 0):
        return json.jsonify({'error': True, 'msg': 'Error while executing the query'})
    # print(form_data)
    print('Normalisation passed')

    if 'farmer_id' not in form_data:
        # save a new farmer
        ret = Queries.save_new_farmer(form_data)
        if(ret == 1):
            return json.jsonify({'error': True, 'msg': last_error})
    else:
        # since we have the farmer_id, it means we have a new farmer, so update the farmer
        ret = Queries.update_farmer(form_data)
        if(ret == 1):
            return json.jsonify({'error': True, 'msg': last_error})

    print('Farmer saved/updated.... ')
    return json.jsonify({'error': False, 'msg': 'Farmer saved successfully'})


@app.route('/toggle_farmer_status', methods=['POST'])
@login_required
def toggle_farmer_status():
    data = request.get_json()
    data['is_active'] = 1 if data['is_active'] == 'yes' else 0

    Queries.toggle_farmer_status(data)
    return json.jsonify({'error': False, 'msg': 'The farmer was updated well'})


# def toggle_farmer_cow_status(farmer_id, status):


@app.route('/toggle_cow_status', methods=['POST'])
@login_required
def toggle_cow_status():
    data = request.get_json()
    Queries.toggle_cow_status(data)
    return json.jsonify({'error': False, 'msg': 'The cow was updated well'})


@app.route('/save_cow', methods=['POST'])
@login_required
def save_cow():
    form_data = request.get_json()

    print('Cow: Validating the passed data')
    ret = Queries.validate_cow(form_data)
    if(ret == 1):
        return json.jsonify({'error': True, 'msg': last_error})
    print('Cow: Validation passed, now lets save the data')

    print('Cow: Normalise the passed data')
    form_data = Queries.normalise_cow(form_data)
    if(form_data == 1):
        return json.jsonify({'error': True, 'msg': last_error})
    print(form_data)
    print('Normalisation passed')

    # since we have the cow_id, update the cow details
    if 'cow_id' in form_data:
        ret = Queries.update_cow(form_data)
        if(ret == 1):
            return json.jsonify({'error': True, 'msg': last_error})
    else:
        ret = Queries.save_new_cow(form_data)
        if(ret == 1):
            return json.jsonify({'error': True, 'msg': last_error})

    print('Cow updated.... ')
    return json.jsonify({'error': False, 'msg': 'Cow saved successfully'})


@app.route('/cf_details', methods=['POST'])
@login_required
def cf_details():
    form_data = request.get_json()
    cf_id = int(form_data['cf_id'])

    # get the cf id details
    cf = Queries.cf_details(cf_id)
    return json.jsonify({'cf': cf})


@app.route('/save_cf', methods=['POST'])
@login_required
def save_cf():
    form_data = request.get_json()

    print('CF: Validating the passed data')
    ret = Queries.validate_cf(form_data)
    if(ret == 1):
        return json.jsonify({'error': True, 'msg': last_error})
    print('Cow: Validation passed, now lets save the data')

    form_data['is_super'] = 1 if form_data['is_super'] == 'yes' else 0

    # since we have the cow_id, update the cow details
    if 'cf_id' in form_data:
        ret = Queries.update_cf(form_data)
        if(ret == 1):
            return json.jsonify({'error': True, 'msg': last_error})
    else:
        ret = Queries.save_new_cf(form_data)
        if(ret == 1):
            return json.jsonify({'error': True, 'msg': last_error})

    print('CF updated.... ')
    return json.jsonify({'error': False, 'msg': 'CF saved successfully'})


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
    # call the Php API that will generate the download file and then serve it...
	print('Generating the cow record stats ....')
	cmd = 'php %s/mod_cron.php farmerData cow_stats TRUE TRUE' % (app.config['NP_PATH'])
	subprocess.call(cmd.split())
	outfile = "%s/CowRecordsBreakdown.csv" % (app.config['NP_PATH'])

	print('Now lets offer the file for download....')
	try:
		return send_file(outfile, attachment_filename='CowRecordsBreakdown.csv', as_attachment = True, mimetype='text/csv')
	except Exception as e:
		raise str(e)


@app.route('/farmer_stats')
@login_required
def farmer_stats():
    # call the Php API that will generate the download file and then serve it...
	print('Generating the usage stats....')
	cmd = 'php %s/mod_cron.php farmerData stats TRUE TRUE' % (app.config['NP_PATH'])
	subprocess.call(cmd.split())
	outfile = '%s/FarmerParticipationStatistics.csv' % (app.config['NP_PATH'])

	print('Now lets offer the file for download....')
	try:
		return send_file(outfile, attachment_filename='FarmerParticipationStatistics.csv', as_attachment = True, mimetype='text/csv')
	except Exception as e:
		raise str(e)


@app.route('/dry_cows')
@login_required
def dry_cows():
    dry_cows = Queries.dry_cows()

    outfile = "%s/DryCows.csv" % (app.config['DASH_PATH'])
    with open(outfile, "w") as f:
        writer = csv.writer(f)
        writer.writerow(['Project','Hub','Farmer Name','Mobile1','Mobile2','CowId','Cow Name','Ear Tag','CF','CF Mobile','Dry Days'])
        writer.writerows(dry_cows)

    try:
        return send_file(outfile, attachment_filename='DryCows.csv', as_attachment = True, mimetype='text/csv')
    except Exception as e:
        return str(e)

@app.route('/canned_queries')
@login_required
def canned_queries():
    return render_template('pending.html')
