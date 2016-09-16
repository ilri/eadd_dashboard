from setuptools import setup, find_packages

setup (
    name='EADD Web Dashboard',
    version='0.1',

    # find the packages automatically
    install_requires=['flask', 'mysqlclient', 'flask-login', 'flask-wtf', 'flask-babel', 'flask-sqlalchemy', 'voluptuous', 'passlib'],
    include_package_data=True,

    author='Wangoru Kihara',
    author_email='soloincc@gmail.com',

    #summary = 'Just another Python package for the cheese shop',
    url='',
    license='GPLv3',
    long_description='A web dashboard for administration of EADD longitudinal survey platform',
)
