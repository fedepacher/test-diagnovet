import peewee
from datetime import datetime

from api.app.model.base_model import BaseModel
from api.app.model.institution_model import Institutions
from api.app.model.patient_model import Patients
from api.app.model.veterinarian_model import Veterinarians
from api.app.model.user_model import Users


class Studies(BaseModel):
    """DB studies columns definition.

    Args:
        BaseModel: Database connection reference.
    """
    id = peewee.AutoField()
    patient = peewee.ForeignKeyField(Patients, backref='studies')
    veterinarian = peewee.ForeignKeyField(Veterinarians, null=True)
    uploaded_by = peewee.ForeignKeyField(Users)
    institutions = peewee.ForeignKeyField(Institutions, backref='studies', null=False)

    study_type = peewee.CharField(max_length=50)  # X-ray, blood test, etc
    study_date = peewee.DateTimeField(null=True)

    observations = peewee.TextField(null=True)
    diagnosis = peewee.TextField(null=True)
    recommendations = peewee.TextField(null=True)

    raw_text = peewee.TextField(null=True)  # extracted OCR/AI text

    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "studies"
