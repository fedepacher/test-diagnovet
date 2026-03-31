""" doc """

import logging

from api.app.model.breed_model import Breeds
from api.app.model.country_model import Countries
from api.app.model.gender_model import Genders
from api.app.model.institution_model import Institutions
from api.app.model.patient_model import Patients
from api.app.model.role_model import Roles
from api.app.model.profile_model import Profiles
from api.app.model.specie_model import Species
from api.app.model.study_model import Studies
from api.app.model.study_image_model import StudyImages
from api.app.model.study_result_model import StudyResults
from api.app.model.user_model import Users
from api.app.model.user_institution_model import UsersInstitutions
from api.app.model.veterinarian_model import Veterinarians
from api.app.utils.db import db


def create_tables():
    """Create DB tables if they do not exist."""
    logging.info("Creating database tables...")
    with db:
        db.create_tables([
            Countries,
            Genders,
            Institutions,
            Patients,
            Roles,
            Profiles,
            Veterinarians,
            UsersInstitutions,
            Users,
            Studies,
            StudyImages,
            StudyResults,
            Species,
            Breeds
        ], safe=True)  # `safe=True` will not raise an exception if tables already exist
