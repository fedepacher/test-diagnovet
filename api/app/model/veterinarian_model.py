import peewee

from api.app.model.base_model import BaseModel
from api.app.model.profile_model import Profiles


class Veterinarians(BaseModel):
    """DB veterinarian columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    profile = peewee.ForeignKeyField(Profiles)
    license_number = peewee.CharField(null=True)

    class Meta:
        table_name = "veterinarians"
