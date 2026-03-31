import peewee

from api.app.model.base_model import BaseModel
from api.app.model.study_model import Studies

class StudyImages(BaseModel):
    """DB study images columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField()
    study = peewee.ForeignKeyField(Studies, backref='images')
    url = peewee.TextField()
    description = peewee.CharField(max_length=255, null=True)

    class Meta:
        table_name = "study_images"
