from peewee import Model

from db.connections import db


class BaseModel(Model):
    class Meta:
        database = db
