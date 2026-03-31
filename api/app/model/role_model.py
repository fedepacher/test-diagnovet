import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel


class Roles(BaseModel):
    """DB roles columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField(primary_key=True)
    name = peewee.CharField(max_length=50, unique=True, null=False)
    spanish_name = peewee.TextField(null=True)
    english_name = peewee.TextField(null=True)
    portuguese_name = peewee.TextField(null=True)
    description = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "roles"

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
