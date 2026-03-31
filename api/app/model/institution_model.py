import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel
from api.app.model.user_model import Users
from api.app.utils.global_def import StatusEnum


class Institutions(BaseModel):
    """DB institution (veterinary centers / organizations).

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField(primary_key=True)
    name = peewee.CharField(max_length=100, null=False)
    email = peewee.CharField(max_length=100, null=True)
    contact_number = peewee.CharField(max_length=20, null=True)
    address = peewee.CharField(max_length=255, null=True)

    created_at = peewee.DateTimeField(default=datetime.now, null=False)
    updated_at = peewee.DateTimeField(default=datetime.now, null=False)
    deleted_at = peewee.DateTimeField(null=True, default=None)

    active = peewee.BooleanField(default=True)
    status = peewee.CharField(max_length=20, default=StatusEnum.ACTIVE, choices=[
        (stats.name, stats.value) for stats in StatusEnum
    ])  # active, inactive, deleted

    created_by = peewee.ForeignKeyField(Users, backref='institutions', null=True)
    updated_by = peewee.ForeignKeyField(Users, backref='institutions', null=True)
    deleted_by = peewee.ForeignKeyField(Users, backref='institutions', null=True)

    class Meta:
        table_name = "institutions"
        indexes = (
            (("name",), False),
            (("active",), False),
            (("status",), False),
        )

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
