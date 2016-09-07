from setuptools import setup, find_packages

setup (
    name='EADD Web Dashboard',
    version='0.1',

    # find the packages automatically
    packages=find_packages(),
    include_package_data=True,

    author='Wangoru Kihara',
    author_email='soloincc@gmail.com',

    #summary = 'Just another Python package for the cheese shop',
    url='',
    license='GPLv3',
    long_description='A web dashboard for administration of EADD longitudinal survey platform',
)
