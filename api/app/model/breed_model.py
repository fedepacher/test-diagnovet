import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel
from api.app.model.specie_model import Species


class Breeds(BaseModel):
    """DB patients columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField(primary_key=True)
    name = peewee.CharField(max_length=100, null=False)
    spanish_name = peewee.TextField(null=True)
    english_name = peewee.TextField(null=True)
    portuguese_name = peewee.TextField(null=True)
    species = peewee.ForeignKeyField(Species, backref='breeds')
    is_mixed = peewee.BooleanField(default=False)
    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'breeds'
        indexes = (
            (("name", "species"), True),  # prevent duplicate breed per species
        )
