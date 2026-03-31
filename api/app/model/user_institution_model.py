import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel
from api.app.model.user_model import Users
from api.app.model.institution_model import Institutions
from api.app.utils.global_def import StatusEnum


class UsersInstitutions(BaseModel):
    """DB user institution columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField()
    institution = peewee.ForeignKeyField(Institutions, backref='user_institutions', null=False)
    user = peewee.ForeignKeyField(Users, backref='user_institutions', null=False)
    created_at = peewee.DateTimeField(default=datetime.now, null=False)
    updated_at = peewee.DateTimeField(default=datetime.now, null=False)
    deleted_at = peewee.DateTimeField(null=True)
    created_by = peewee.ForeignKeyField(Users, backref='user_institutions', null=True)
    updated_by = peewee.ForeignKeyField(Users, backref='user_institutions', null=True)
    deleted_by = peewee.ForeignKeyField(Users, backref='user_institutions', null=True)
    status = peewee.CharField(max_length=20, default=StatusEnum.ACTIVE, choices=[
            (stats.name, stats.value) for stats in StatusEnum
        ])  # active, inactive, deleted
    active = peewee.BooleanField(default=True, null=False)

    class Meta:
        table_name = "users_institutions"

    def save(self, *args, **kwargs):
        """Update the updated_at timestamp on save."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
