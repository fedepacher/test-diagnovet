import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel
from api.app.model.gender_model import Genders
from api.app.model.country_model import Countries
from api.app.model.role_model import Roles


class Profiles(BaseModel):
    """DB profile columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField()
    email = peewee.CharField(max_length=50, null=True)
    name = peewee.CharField(max_length=50, null=False)
    last_name = peewee.CharField(max_length=50, null=False)
    document_number = peewee.CharField(max_length=50, null=True)
    contact_number = peewee.CharField(max_length=15, null=True)
    birthdate = peewee.DateField(null=True)
    gender = peewee.ForeignKeyField(Genders, backref='profiles', null=True)
    country = peewee.ForeignKeyField(Countries, backref='profiles', null=True)
    updated_at = peewee.DateTimeField(default=datetime.now, null=False)
    created_at = peewee.DateTimeField(default=datetime.now, null=False)
    deleted_at = peewee.DateTimeField(null=True, default=None)
    role = peewee.ForeignKeyField(Roles, backref='profiles', null=True)

    class Meta:
        """ doc """
        table_name = "profiles"
        indexes = (
            (("email",), False),
            (("document_number",), False),
            (("last_name", "name"), False),
        )

    def save(self, *args, **kwargs):
        """Update the updated_at timestamp on save."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
