import peewee

from api.app.utils.db import db


class BaseModel(peewee.Model):
    class Meta:
        database = db
