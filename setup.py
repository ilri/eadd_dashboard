from setuptools import setup, find_packages

setup (
       name='eadd_web_dashboard',
       version='0.1',
       packages=find_packages(),

       # Declare your packages' dependencies here, for eg:
       install_requires=['foo>=3'],

       # Fill in these to make your Egg ready for upload to
       # PyPI
       author='Wangoru Kihara',
       author_email='soloincc@gmail.com',

       #summary = 'Just another Python package for the cheese shop',
       url='',
       license='GPLv3',
       long_description='A web dashboard for the administration of EADD longitudinal survey',

       # could also include long_description, download_url, classifiers, etc.


       )