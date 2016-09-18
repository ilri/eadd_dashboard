from voluptuous import Schema, Required, Invalid, All, Match, Length, Any
from datetime import datetime

from dash import app
from .sql import Dbase

# create the db connection
db = Dbase(
    app.config['DBHOST'],
    app.config['DBUSERNAME'],
    app.config['DBPASSWORD'],
    app.config['DBNAME']
)

class Queries:

    def farmer_tree_data(self):
        db.curQuery = """
        select
            location_district as id, location_district as text, "-1" as parentid, 1 as is_active
        from farmer
        where extension_personnel_id not in(13,2) and project like 'eadd%' and project not like '%test%'
            and location_district is not null and location_district != ""
        group by location_district
        order by project, location_district
        """
        all_locations = db.dictQuery()

        # get all the farmers
        db.curQuery = """
        select
            id as id, name as text, location_district as parentid, is_active
        from farmer
        where location_district is not null and location_district != "" and project not like "%test%"
            and extension_personnel_id not in (13,2)  and project like "eadd%"
        order by name
        """
        all_farmers = db.dictQuery()

        return all_locations + all_farmers

    def farmer_details(self, farmer_id):
        # get the farmer id details
        db.curQuery = """
        select
          a.id as farmer_id, a.name as farmer_name, a.mobile_no, a.mobile_no2, a.location_district as hub, a.hh_id, a.gps_longitude, a.gps_latitude, a.pref_locale as locale, b.name as cf, if(is_active = 1, 'Yes', 'No') as is_active
        from farmer as a inner join extension_personnel as b on a.extension_personnel_id = b.id
        where a.id = %d
        """ % (farmer_id)
        farmer = db.dictQuery()

        db.curQuery = """
        select
          id as cow_id, name as cow_name, ear_tag_number as ear_tag, date_of_birth as dob, sex, breed_group, sire_id, dam_id, milking_status as is_milking, if(in_calf=1,'Yes','No') as is_incalf, parity, if(farmer_id = 0, 'No', 'Yes') as is_active
        from cow
        where farmer_id = %d or old_farmer_id = %d
        """  % (farmer_id, farmer_id)
        cows = db.dictQuery()

        return {'farmer': farmer[0], 'animals': cows}


    def all_farmers(self, criteria):
        db.curQuery = """
        select id, name from farmer where name like '%s' order by name
        """ % ('%' + criteria + '%')
        farmers = db.dictQuery()

        farmers = cursor.fetchall()
        suggestions = []
        for f in farmers:
            data = {'id': f['id'], 'name': f['name'], 'module': 'farmers'}
            suggestions.append({'data': data, 'value': f['name']})

        return suggestions


    def all_cfs(self, criteria):
        db.curQuery = """
        select id as cf_id, name from extension_personnel where name like '%s' order by name
        """ % ('%' + criteria + '%')
        cfs = db.dictQuery()

        suggestions = []
        for cf in cfs:
            suggestions.append({'data': cf['name'], 'value': cf['name']})

        return suggestions


    def all_locales(self, criteria):
        db.curQuery = """
        select language from locales where prefix like '%s' or language like '%s' order by language
        """ % ('%' + criteria + '%', '%' + criteria + '%')
        locales = db.dictQuery()

        suggestions = []
        for loc in locales:
            suggestions.append({'data': loc['language'], 'value': loc['language']})

        return suggestions


    def all_hubs(self, criteria):
        db.curQuery = """
        select location_district as hub from farmer where location_district like '%s' group by location_district order by location_district
        """ % ('%' + criteria + '%')
        hubs = db.dictQuery()

        suggestions = []
        for hub in hubs:
            suggestions.append({'data': hub['hub'], 'value': hub['hub']})

        return suggestions


    def all_breeds(self, criteria):
        db.curQuery = """
        select breed_group as breed from cow where breed_group like '%s' group by breed_group order by breed_group
        """ % ('%' + criteria + '%')
        breeds = db.dictQuery()

        suggestions = []
        for breed in breeds:
            suggestions.append({'data': breed['breed'], 'value': breed['breed']})

        return suggestions


    def all_milking_statuses(self, criteria):
        db.curQuery = """
        select milking_status as milk_status from cow where milking_status like '%s' group by milking_status order by milking_status
        """ % ('%' + criteria + '%')
        milk_statuses = db.dictQuery()

        suggestions = []
        for milk_status in milk_statuses:
            suggestions.append({'data': milk_status['milk_status'], 'value': milk_status['milk_status']})

        return suggestions


    def global_search(self, criteria):
        # search from the farmers table
        query = """
        select id, name, hh_id, location_district as hub, mobile_no, mobile_no2
        from farmer
        where name like '%s' or hh_id like '%s' or location_district like '%s' or mobile_no like '%s' or mobile_no2 like '%s'
        order by name
        """
        cr = '%' + criteria + '%'
        vals = (cr, cr, cr, cr, cr)
        db.curQuery = query % vals
        farmers = db.dictQuery()

        suggestions = []
        for f in farmers:
            f['hhid1'] = '' if f['hh_id'] is None else f['hh_id']
            f['mobile2'] = '' if f['mobile_no2'] is None else f['mobile_no2']
            value = "Farmer: %(name)s %(hub)s %(hhid1)s %(mobile_no)s %(mobile2)s" % f

            data = {'category': 'Farmer', 'id': f['id'], 'module': 'global_search'}
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
        db.curQuery = query % vals

        cows = db.dictQuery()
        for c in cows:
            c['ear_tag1'] = '' if c['ear_tag'] is None else c['ear_tag']
            c['farmer_id'] = c['old_farmer_id'] if c['farmer_id'] == 0 else c['farmer_id']
            value = "Cow: %(name)s %(ear_tag1)s" % c
            data = {'category': 'Cow', 'id': c['id'], 'module': 'global_search', 'farmer_id': c['farmer_id']}
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
        db.curQuery = query % vals

        cfs = db.dictQuery()
        for c in cfs:
            value = "CF: %(name)s %(mobile_no)s" % c
            data = {'category': 'CF', 'id': c['id'], 'module': 'global_search'}
            suggestions.append({'value': value, 'data': data})

        return suggestions

    def normalise_farmer(self, data):
        """
        Normalise the data passed from the user, by converting the options to FK, indices etc
        """
        # check that the locale is made up of 2 letters only
        if(len(data['locale']) != 2):
            db.curQuery = "select prefix from locales where language = '%s'" % (data['locale'])
            locale = db.dictQuery()
            data['locale'] = locale[0]['prefix']

        # check that the cf is an integer
        if not data['cf'].isdigit():
            db.curQuery = "select id from extension_personnel where name = '%s'" % (data['cf'])
            cf = db.dictQuery()
            data['cf'] = cf[0]['id']

        # get the project based on the farmer hub
        db.curQuery = 'select project from farmer where location_district = "%s"' % (data['hub'])
        project = db.dictQuery()
        data['project'] = project[0]['project']

        # normalise whether the farmer is active
        if(data['is_active'].isalpha()):
            data['is_active'] = 1 if data['is_active'] == 'yes' else 0

        return data


    def validate_farmer(self, form_data):
        # define our constraints
        validator = Schema({
            Required('csrf_token'): All(str),
            'farmer_id': All(int, msg='Invalid farmer id. Stop tampering with the system.'),
            Required('farmer_name'): All(str, Length(min=7, max=25), msg='The farmer name should have 7-25 characters'),
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
            raise e.msg
        return 0


    def update_farmer(self, data):
        vals = (data['farmer_name'], data['mobile_no'], data['hub'], data['gps_lon'], data['gps_lat'],
                int(data['cf']), data['locale'], data['is_active'], data['mobile_no1'], data['project'], int(data['farmer_id']))
        db.curQuery = """
            update farmer set
                name ='%s', mobile_no = '%s', location_district = '%s', gps_longitude = '%s', gps_latitude = '%s',
                extension_personnel_id = %d, pref_locale = '%s', is_active = %d, mobile_no2 = '%s', project = '%s'
            where id = %d
        """ % vals
        db.query()
        return 0


    def save_new_farmer(self, data):
        query = """
            insert into
            farmer(name, mobile_no, location_district, gps_latitude, gps_longitude, extension_personnel_id, pref_locale, is_active, mobile_no2, date_added, project)
            values('%s',  '%s', '%s', '%s', '%s', %d, '%s', %d, '%s', '%s', '%s')
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%i:%s')
        vals = (data['farmer_name'], data['mobile_no'], data['hub'], data['gps_lat'], data['gps_lon'],
                int(data['cf']), data['locale'], data['is_active'], data['mobile_no1'], now, data['project'])
        db.curQuery = query % vals
        db.query()
        return 0


    def validate_cow(self, form_data):
        # define our constraints
        validator = Schema({
            Required('farmer_id'): All(int, msg='Missing farmer id. Stop tampering with the system.'),
            'cow_id': All(int, msg='Missing cow id. Stop tampering with the system.'),
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
        try:
            validator(form_data)
        except Invalid as e:
            raise e.msg
        return 0


    def normalise_cow(self, data):
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


    def update_cow(self, data):
        query = """
            update cow set
                name ='%s', ear_tag_number = '%s', date_of_birth = '%s', sex = '%s', breed_group = '%s',
                milking_status = '%s', in_calf = '%s', parity = %d
            where id = %d
        """
        vals = (data['cow_name'], data['ear_tag'], data['dob'], data['sex'], data['breed_group'],
                data['milking_status'], data['is_incalf'], data['parity'], int(data['cow_id']))
        db.curQuery = query % vals
        db.query()

        # update the farmer_id if there is need
        if(data['is_active'] == 'no'):
            query = 'update cow set old_farmer_id = %d, farmer_id = 0 where id = %d'
            vals = (int(data['farmer_id']), int(data['cow_id']))
            db.curQuery = query % vals
            db.query()

        return 0


    def save_new_cow(self, data):
        query = """
            insert into
            cow(farmer_id, name, ear_tag_number, date_of_birth, sex, breed_group, milking_status, in_calf, parity, datetime_added)
            values(%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, '%s')
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%i:%s')
        vals = (data['farmer_id'], data['cow_name'], data['ear_tag'], data['dob'], data['sex'], data['breed_group'],
                data['milking_status'], data['is_incalf'], data['parity'], now)
        db.curQuery = query % vals

        db.query()
        return 0


    def validate_cf(self, form_data):
        # define our constraints
        validator = Schema({
            Required('csrf_token'): All(str),
            'cf_id': All(int, msg='Invalid CF id. Stop tampering with the system.'),
            Required('cf_name'): All(str, Length(min=3, max=25), msg='The CF name should have 3-25 characters'),
            Required('cf_mobile_no'): All(Match('^(25[456]|0)\d{9}$', msg="Mobile should be like '254700123456'")),
            'cf_mobile_no1': Any(Match('^(25[456]|0)\d{9}$', msg="Mobile should be like '254700123456'"), ''),
            Required('is_super'): All(str, Any('yes', 'no'), msg='Select whether the CF is a super CF or not')
        })

        try:
            validator(form_data)
        except Invalid as e:
            print(e.msg)
            raise e.msg
        return 0


    def update_cf(self, data):
        print('Updating the CF...')
        query = """
            update extension_personnel set
                name ='%s', mobile_no = '%s', mobile_no2 = '%s', is_super = %d
            where id = %d
        """
        vals = (data['cf_name'], data['cf_mobile_no'], data['cf_mobile_no1'], data['is_super'], int(data['cf_id']))
        db.curQuery = query % vals

        db.query()


    def save_new_cf(self, data):
        query = """
            insert into
            extension_personnel(name, mobile_no, mobile_no2, is_super, date_added)
            values('%s', '%s', '%s', %d, '%s')
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%i:%s')
        vals = (data['cf_name'], data['cf_mobile_no'], data['cf_mobile_no1'], int(data['is_super']), now)
        db.curQuery = query % vals

        db.query()


    def cf_details(self, cf_id):
        db.curQuery = """
        select
          a.id as cf_id, a.name as cf_name, a.mobile_no, a.mobile_no2, if(is_super = 1, 'Yes', 'No') as is_super
        from extension_personnel as a
        where a.id = %d
        """ % (cf_id)
        cf = db.dictQuery()

        return cf

    def toggle_cow_status(self, data):
        if(data['is_active'] == 'no'):
            query = 'update cow set old_farmer_id = %d, farmer_id = 0 where id = %d'
            vals = (int(data['farmer_id']), int(data['cow_id']))
            db.curQuery = query % vals
            db.query()
        else:
            query = 'update cow set old_farmer_id = NULL, farmer_id = %d where id = %d'
            vals = (int(data['farmer_id']), int(data['cow_id']))
            db.curQuery = query % vals
            db.query()


    def toggle_farmer_status(self, data):
        query = 'update farmer set is_active = %d where id = %d'
        vals = (int(data['is_active']), int(data['farmer_id']))
        db.curQuery = query % vals
        db.query()


    def dry_cows(self):
        db.curQuery = """
            select
				b.*, datediff(now(), event_date) as 'Dry Days'
			from cow_event as a inner join (
				SELECT
					b.project, b.location_district, b.name as 'Farmer Name', b.mobile_no as 'Mobile1', b.mobile_no2 as 'Mobile2', a.id as 'CowId', a.name as 'Cow Name', a.ear_tag_number as 'Ear Tag', c.name as 'CF', c.mobile_no as 'CF Mobile'
				FROM cow as a inner join farmer as b on a.farmer_id = b.id inner join extension_personnel as c on b.extension_personnel_id = c.id
				where b.project in ('eadd_ug') and sex = 'Female' and milking_status = 'adult_not_milking' and b.is_active = 1
			) as b on a.cow_id =b.CowId and a.event_id = 7 and datediff(now(), event_date) > 20
		"""
        dry_cows = db.query()
        return dry_cows
