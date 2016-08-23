#!flask/bin/python
import os
import unittest

from config import basedir
from dash import app, db
from app.models import User

class TestCase(unittest.TestCase):
    def tearDown(self):
        db.session.remove()
        db.drop_all()