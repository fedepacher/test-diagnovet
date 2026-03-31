import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel
from api.app.model.profile_model import Profiles
from api.app.model.role_model import Roles
from api.app.utils.global_def import StatusEnum


class Users(BaseModel):
    """DB user columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField()
    username = peewee.CharField(max_length=50, null=False)
    password = peewee.CharField(max_length=200, null=True)
    email = peewee.CharField(max_length=50, unique=True, null=False)
    created_at = peewee.DateTimeField(default=datetime.now, null=False)
    updated_at = peewee.DateTimeField(default=datetime.now, null=False)
    deleted_at = peewee.DateTimeField(null=True, default=None)
    active = peewee.BooleanField(null=True)
    status = peewee.CharField(max_length=20, default=StatusEnum.ACTIVE, null=True)
    profile = peewee.ForeignKeyField(Profiles, backref='users', null=True)

    class Meta:
        table_name = "users"

    def save(self, *args, **kwargs):
        """Update the updated_at timestamp on save."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
