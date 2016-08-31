from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from dash import app
import datetime
from flask import json

Base = declarative_base()
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
metadata = MetaData(bind=engine)


def now():
    """ Get the current date/time """
    return datetime.datetime.now()


class BaseClass():
    def to_json(inst, cls):
        """
        Jsonify the sql alchemy query result.
        """
        print("still doing this...")
        convert = dict()
        # add your coversions for things like datetime's
        # and what-not that aren't serializable.
        d = dict()
        for c in cls.__table__.columns:
            v = getattr(inst, c.name)
            if c.type in convert.keys() and v is not None:
                try:
                    d[c.name] = convert[c.type](v)
                except:
                    d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
            elif v is None:
                d[c.name] = str()
            else:
                d[c.name] = v
        return json.dumps(d)


class Farmer(Base, BaseClass):
    __table__ = Table('farmer', metadata, autoload=True)

    def jsonify_me(self):
        return self.to_json(self)

    def __repr__(self):
        return self.to_json(self)


class ExtensionPersonnel(Base):
    __table__ = Table('extension_personnel', metadata, autoload=True)

    def __repr__(self):
        return '<Extension Personnel %r>' % (self.name)
