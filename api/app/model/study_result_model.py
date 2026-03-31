import peewee

from api.app.model.base_model import BaseModel
from api.app.model.study_model import Studies


class StudyResults(BaseModel):
    """DB study results columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField()
    study = peewee.ForeignKeyField(Studies, backref='study_results')

    key = peewee.CharField(max_length=100)  # e.g. "glucose"
    value = peewee.CharField(max_length=50)
    unit = peewee.CharField(max_length=20, null=True)
    reference_range = peewee.CharField(max_length=50, null=True)

    class Meta:
        table_name = "study_results"
