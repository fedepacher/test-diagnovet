import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel


class Species(BaseModel):
    """DB species columns definition.

        Args:
            BaseModel: Database connection reference.
        """
    id = peewee.AutoField(primary_key=True)
    name = peewee.CharField(max_length=50, unique=True, null=False)
    spanish_name = peewee.TextField(null=True)
    english_name = peewee.TextField(null=True)
    portuguese_name = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "species"
