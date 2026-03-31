import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel
from api.app.model.breed_model import Breeds
from api.app.model.institution_model import Institutions
from api.app.model.gender_model import Genders
from api.app.model.profile_model import Profiles
from api.app.model.specie_model import Species
from api.app.model.user_model import Users
from api.app.utils.global_def import StatusEnum


class Patients(BaseModel):
    """DB patients columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField()
    name = peewee.CharField(max_length=100)
    species = peewee.ForeignKeyField(Species, null=True)
    breed = peewee.ForeignKeyField(Breeds, null=True)
    age = peewee.CharField(max_length=20)
    gender = peewee.ForeignKeyField(Genders, null=True)
    is_neutered = peewee.BooleanField(null=True)
    owner = peewee.ForeignKeyField(Profiles, backref='patients', null=True)
    institution = peewee.ForeignKeyField(Institutions, backref='patients', null=False)
    active = peewee.BooleanField(default=True)
    status = peewee.CharField(max_length=20, default=StatusEnum.ACTIVE, choices=[
        (stats.name, stats.value) for stats in StatusEnum
    ])  # active, inactive, deleted
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now, null=False)
    deleted_at = peewee.DateTimeField(null=True, default=None)
    updated_by = peewee.ForeignKeyField(Users, backref='patients', null=True)
    created_by = peewee.ForeignKeyField(Users, backref='patients', null=True)
    deleted_by = peewee.ForeignKeyField(Users, backref='patients', null=True)

    class Meta:
        table_name = "patients"
