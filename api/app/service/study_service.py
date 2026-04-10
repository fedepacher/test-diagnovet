import logging
from typing import List
from fastapi import HTTPException, Request, status
from peewee import JOIN

from api.app.schema import patient_schema, study_schema, professional_schema
from api.app.model.patient_model import Patients as PatientModel
from api.app.model.profile_model import Profiles as ProfileModel
from api.app.model.study_model import Studies as StudyModel
from api.app.model.study_image_model import StudyImages as StudyImagesModel
from api.app.model.study_result_model import StudyResults as StudyResultsModel
from api.app.model.veterinarian_model import Veterinarians as VeterinarianModel
from api.app.utils.functions import get_language_attr, translate


async def get_all_studies(institution_id: int, patient_id: int) -> List[study_schema.StudyBase]:
    """
    Retrieve all the studies associated with the given patient and institution.

    Args:
        institution_id (int): Patient ID
        patient_id (int): Patient ID

    Returns:
        List[study_schema.StudyBase]: List of study objects.
    """
    patient_exists = (
        PatientModel
        .select()
        .where(
            (PatientModel.id == patient_id) &
            (PatientModel.institution == institution_id) &
            (PatientModel.deleted_at.is_null())
        )
        .exists()
    )

    if not patient_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found in institution {institution_id}"
        )

    query = (
        StudyModel
        .select(
            StudyModel.id,
            StudyModel.study_type,
        )
        .where(
            (StudyModel.patient == patient_id) &
            (StudyModel.institutions == institution_id)
        )
        .order_by(StudyModel.study_date.desc(nulls="LAST"))
        .dicts()
    )

    study_list = []
    for row in query:
        try:
            study_data = study_schema.StudyBase(**row)
            study_list.append(study_data)
        except ValueError as e:
            logging.error(f"Skipping study due to transformation error: {e}")
            continue

    logging.info(f"Successfully obtained {len(study_list)} studies form patient {patient_id}")
    return study_list


async def get_study_result(institution_id: int, result_id: int, accept_language: str) -> study_schema.StudyDetailSchema:
    """
    Get study result for the given patient and institution.

    Args:
        institution_id (int): Patient ID
        result_id (int): Patient ID
        accept_language

    Returns:
        study_schema.StudyBase: Study object.
     """
    lang_attr = get_language_attr(accept_language)

    # Get studies and relationship
    study = (
        StudyModel
        .select(
            StudyModel,
            PatientModel,
            VeterinarianModel,
            ProfileModel  # profile del vet
        )
        .join(PatientModel)
        .switch(StudyModel)
        .join(VeterinarianModel, JOIN.LEFT_OUTER)
        .join(ProfileModel, JOIN.LEFT_OUTER, on=(VeterinarianModel.profile == ProfileModel.id))
        .where(
            (StudyModel.id == result_id) &
            (StudyModel.institutions == institution_id)
        )
        .first()
    )

    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study {result_id} not found"
        )

    # Get results
    results = (
        StudyResultsModel
        .select()
        .where(StudyResultsModel.study == study.id)
        .dicts()
    )

    # Get images
    images = (
        StudyImagesModel
        .select()
        .where(StudyImagesModel.study == study.id)
        .dicts()
    )

    # Get vet
    veterinarian_data = None
    if study.veterinarian and study.veterinarian.profile:
        profile = study.veterinarian.profile
        veterinarian_data = {
            "name": profile.name,
            "last_name": profile.last_name,
            "license_number": study.veterinarian.license_number
        }

    # Get patient
    patient = study.patient
    patient_data = {
        "name": patient.name,
        "specie": translate(patient.species, lang_attr),
        "breed": translate(patient.breed, lang_attr),
        "age": patient.age,
        "gender": translate(patient.gender, lang_attr),
        "is_neutered": patient.is_neutered
    }

    return study_schema.StudyDetailSchema(
                id=study.id,
                study_type=study.study_type,
                study_date=study.study_date,
                observations=study.observations,
                diagnosis=study.diagnosis,
                recommendations=study.recommendations,
                created_at=study.created_at,
                patient=patient_schema.PatientInfo(**patient_data) if patient_data else None,
                veterinarian=professional_schema.ProfessionalInfo(**veterinarian_data) if veterinarian_data else None,
                results=list(results),
                images=list(images)
            )