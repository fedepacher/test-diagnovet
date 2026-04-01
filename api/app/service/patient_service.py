import asyncio
import logging
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
from fastapi.concurrency import run_in_threadpool
from peewee import fn, JOIN
from typing import List, Optional

from api.app.schema import patient_schema, profile_schema, user_schema
from api.app.model.breed_model import Breeds as BreedsModel
from api.app.model.country_model import Countries as CountryModel
from api.app.model.gender_model import Genders as GenderModel
from api.app.model.institution_model import Institutions as InstitutionModel
from api.app.model.patient_model import Patients as PatientModel
from api.app.model.profile_model import Profiles as ProfileModel
from api.app.model.role_model import Roles as RoleModel
from api.app.model.specie_model import Species as SpeciesModel
from api.app.model.study_model import Studies as StudyModel
from api.app.model.study_image_model import StudyImages as StudyImageModel
from api.app.model.study_result_model import StudyResults as StudyResultModel
from api.app.model.veterinarian_model import Veterinarians as VeterinarianModel
from api.app.utils.global_def import StatusEnum, ResultEnum
from api.app.utils.functions import (check_if_id_exist,
                                     get_language_fields,
                                     extract_images_from_pdf,
                                     extract_text_from_pdf,
                                     get_model_id,
                                     normalize_breed,
                                     normalize_species,
                                     parse_gender,
                                     save_file,
                                     )
from api.app.utils.ai_function import call_llm, QuotaExhaustedError
from api.app.utils.db import db


MAX_CONCURRENT_TASKS = 3


def create_patient(
    patient: patient_schema.PatientCreateForm,
    institution_id: int,
    user: user_schema.User
) -> patient_schema.PatientResponse:
    """
    Create a new patient in the database or reactivate a previously deleted patient.

    Args:
        patient: Complete patient data including personal information
        institution_id: Institution ID
        user: User creating the patient (for permissions and audit trail)

    Returns:
        PatientResponse: Created or reactivated patient ID with success status

    Raises:
        HTTPException 400: Email already registered for active patient
        HTTPException 500: Database or file system errors during creation
    """
    logging.info(f"Checking existing profile for {patient.patient.name}")

    existing_profile = (
        ProfileModel
        .select()
        .where(
            (ProfileModel.name == patient.owner.name) &
            (ProfileModel.last_name == patient.owner.last_name)
        )
        .first()
    )
    if existing_profile:
        logging.info(f"Profile for owner {patient.owner.last_name} exists.")

        existing_patient = PatientModel.select().where(
            (PatientModel.owner == existing_profile.id) &
            (PatientModel.institution == institution_id) &
            (PatientModel.name == patient.patient.name)
        ).first()

        if existing_patient:
            if existing_patient.deleted_by_id is None:
                msg = f"Patient {patient.patient.name} is already registered for the user {user.username}."
                logging.debug(msg)
                return patient_schema.PatientResponse(
                    id=existing_patient.id,
                    status=ResultEnum.SUCCESS
                )
            else:
                logging.info(
                    f"Reactivating patient {patient.patient.name} previously deleted by "
                    f"user: {existing_patient.deleted_by_id}.")
                reactivate_patient(existing_patient, user.id)
                return patient_schema.PatientResponse(id=existing_patient.id, status=ResultEnum.SUCCESS)

        else:
            logging.info(f"Creating new patient record {patient.patient.name} for user {user.username}.")
            return create_new_patient(existing_profile.id, user, patient.patient, institution_id=institution_id)

    else:
        logging.info(f"Creating new profile for {patient.owner.contact_email}.")
        try:
            profile_id = create_profile(patient.owner, user)
            return create_new_patient(profile_id, user, patient.patient, institution_id=institution_id)
        except Exception as e:
            logging.error(f"Error creating profile: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="An error occurred while creating the patient.")


def reactivate_patient(patient: PatientModel, user_id: int) -> None:
    """
    Reactivate a previously soft-deleted patient.

    Args:
        patient: Patient model instance to reactivate
        user_id: ID of user performing the reactivation

    Raises:
        HTTPException 500: Database error during reactivation
    """
    try:
        patient.updated_by_id = user_id
        patient.updated_at = datetime.now()
        patient.deleted_by_id = None
        patient.deleted_at = None
        patient.status = StatusEnum.ACTIVE.value
        patient.save()
        logging.info(f"patient {patient.id} reactivated with status: {patient.status}")
    except Exception as e:
        logging.error(f"Error reactivating patient: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An error occurred while reactivating the patient.")


def create_profile(patient: profile_schema.Profile, user: user_schema.User) -> int:
    """
    Create a new profile in the database and return its ID.

    Handles optional fields gracefully by only setting non-None values.

    Args:
        patient: Patient input data with optional fields
        user: User creating the profile

    Returns:
        int: Created profile ID
    """
    try:
        profile_data = {
            'email': patient.contact_email,
            'name': patient.name,
            'last_name': patient.last_name,
            'updated_at': datetime.now(),
            'created_at': datetime.now(),
            'updated_by': user.id,
            'created_by': user.id,
            'deleted_by': None
        }

        if patient.document_number is not None:
            profile_data['document_number'] = patient.document_number
        if patient.contact_number is not None:
            profile_data['contact_number'] = patient.contact_number
        if patient.birthdate is not None:
            profile_data['birthdate'] = patient.birthdate
        if patient.country and patient.country.country_id:
            check_if_id_exist(patient.country.country_id, CountryModel)
            profile_data['country'] = patient.country.country_id
        if patient.gender and patient.gender.gender_id:
            check_if_id_exist(patient.gender.gender_id, GenderModel)
            profile_data['gender'] = patient.gender.gender_id
        if patient.role and patient.role.role_id:
            check_if_id_exist(patient.role.role_id, RoleModel)
            profile_data['role_id'] = patient.role.role_id

        profile = ProfileModel.create(**profile_data)
        logging.info(f"Profile for {patient.contact_email} created with ID {profile.id}.")
        return profile.id

    except Exception as e:
        logging.error(f"Error creating profile for {patient.contact_email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )


def create_new_patient(
    profile_id: int, user: user_schema.User,
    patient: patient_schema.PatientInput,
    institution_id: int
) -> patient_schema.PatientResponse:
    """Create a new patient entry in the database with consistent status values."""
    try:
        with db.atomic():
            new_patient = PatientModel(
                name=patient.name,
                species=patient.specie,
                breed=patient.breed,
                age=patient.age,
                gender=patient.gender_id,
                is_neutered=patient.is_neutered,
                owner=profile_id,
                institution_id=institution_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                deleted_at=None,
                updated_by=user.id,
                created_by=user.id,
                deleted_by=None,
                active=True,
                status=StatusEnum.ACTIVE.value,
            )

            new_patient.save()
            logging.info(f"Created patient {new_patient.id} with status: {new_patient.status}")

    except Exception as e:
        logging.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An error occurred while creating the patient.")

    return patient_schema.PatientResponse(id=new_patient.id, status=ResultEnum.SUCCESS)


async def get_patients(
    user: user_schema.User,
    institution_id: int = 0,
    name: str = '',
    accept_language: str = 'en',
) -> List[patient_schema.PatientBasicData]:
    """
    Get all the user's patients in the DB.

    Args:
        user (user_schema.User): User.
        institution_id (int): Institution ID.
        name (str): Patient's name.
        accept_language (str): LLanguage.

    Returns:
        list: List of patients filtered by user.
    """
    logging.info(f"Getting patients for user: {user.username}")
    language_fields = get_language_fields(accept_language)

    query = (
        PatientModel
        .select(
            PatientModel.id,
            PatientModel.name,
            PatientModel.age,
            PatientModel.is_neutered,
            PatientModel.active,
            PatientModel.status,
            language_fields["specie"].alias("specie"),
            language_fields["breed"].alias("breed"),
            language_fields["gender"].alias("gender"),
            InstitutionModel.name.alias("institution"),
        )
        .join(InstitutionModel)
        .switch(PatientModel)
        .join(SpeciesModel, JOIN.LEFT_OUTER)
        .switch(PatientModel)
        .join(BreedsModel, JOIN.LEFT_OUTER)
        .switch(PatientModel)
        .join(GenderModel, JOIN.LEFT_OUTER)
        .where(
            (PatientModel.institution == institution_id) &
            (PatientModel.deleted_at.is_null())
        )
        .order_by(PatientModel.name.asc())
    )

    if name:
        query = query.where(
            fn.LOWER(PatientModel.name).contains(name.lower())
        )

    patient_list = []
    for row in query.dicts():
        try:
            patient_data = patient_schema.PatientBasicData(**row)
            patient_list.append(patient_data)
        except ValueError as e:
            logging.error(f"Skipping patient due to transformation error: {e}")
            continue

    logging.info(f"Successfully transformed {len(patient_list)} patients")
    return patient_list


def get_patient(
        patient_id: int,
        institution_id: int,
        user: user_schema.User,
        accept_language: str
) -> patient_schema.PatientBasicData:
    """
    Retrieves a patient's data by email or ID for a given user.

    Updated with proper handling and better error management.

    Args:
        patient_id (int): ID of the patient.
        institution_id (int): ID of the institution.
        user (user_schema.User): Authenticated user object.
        accept_language (str): Language preference for localized fields.

    Returns:
        patient_schema.PatientBasicData: Complete patient.

    Raises:
        HTTPException: If the patient is not found or an unexpected error occurs.
        ValueError: If both patient_email and patient_id are missing, or user is None.
    """
    language_fields = get_language_fields(accept_language)

    logging.info(f"Getting patient {patient_id} for user {user.username}")

    query = (
        PatientModel
        .select(
            PatientModel.id,
            PatientModel.name,
            PatientModel.age,
            PatientModel.is_neutered,
            PatientModel.active,
            PatientModel.status,
            language_fields["specie"].alias("specie"),
            language_fields["breed"].alias("breed"),
            language_fields["gender"].alias("gender"),
            InstitutionModel.name.alias("institution"),
        )
        .join(InstitutionModel)
        .switch(PatientModel)
        .join(SpeciesModel, JOIN.LEFT_OUTER)
        .switch(PatientModel)
        .join(BreedsModel, JOIN.LEFT_OUTER)
        .switch(PatientModel)
        .join(GenderModel, JOIN.LEFT_OUTER)
        .where(
            (PatientModel.id == patient_id) &
            (PatientModel.institution == institution_id) &
            (PatientModel.deleted_at.is_null())
        )
        .dicts()
        .first()
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found in institution {institution_id}"
        )

    return patient_schema.PatientBasicData(**query)


def safe_get_optional_int(value) -> Optional[int]:
    """
    Safely convert database value to Optional[int].

    Handles NULL/None values from database foreign keys that allow NULL.

    Args:
        value: Database value (could be int, None, or string representation)

    Returns:
        Optional[int]: Integer value or None if input was NULL/None
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        logging.warning(f"Could not convert value to int: {value}")
        return None


def save_to_db_without_images(institution_id, data, user):
    with db.atomic():

        # OWNER → Profile
        owner_data = data.get("owner", {})
        patient_data = data.get("patient", {})
        vet_data = data.get("veterinarian", {})

        # Patient
        gender, neutered = parse_gender(patient_data.get("gender"))
        specie = normalize_species(patient_data.get("species", None))
        breed = normalize_breed(patient_data.get("breed", None))

        gender_id = get_model_id(gender, GenderModel)
        specie_id = get_model_id(specie, SpeciesModel)
        breed_id = get_model_id(breed, BreedsModel)

        patient_form = patient_schema.PatientCreateForm(
            owner=profile_schema.Profile(
                contact_email=owner_data.get("email") or None,
                name=owner_data.get("name") or "Unknown",
                last_name=owner_data.get("last_name") or "Unknown",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            patient=patient_schema.PatientInput(
                name=patient_data.get("name") or "Unknown",
                specie=specie_id,
                breed=breed_id,
                age=patient_data.get("age") or "Unknown",
                gender_id=gender_id,
                is_neutered=patient_data.get("neutered") or neutered,
            )
        )

        patient = create_patient(
            patient_form,
            institution_id,
            user
        )

        # Veterinarian (Profile)
        if vet_data:
            vet_profile, _ = ProfileModel.get_or_create(
                name=vet_data.get("name", "Unknown"),
                last_name=vet_data.get("last_name", "")
            )
            veterinarian, _ = VeterinarianModel.get_or_create(
                profile=vet_profile.id,
                license_number=vet_data.get("license_number", "")
            )

        # Study
        study_data = data.get("study", {})

        study = StudyModel.create(
            patient=patient.id,
            veterinarian=veterinarian.id,
            uploaded_by=user,
            institutions=institution_id,
            study_type=study_data.get("type"),
            study_date=study_data.get("date"),
            observations=data.get("observations"),
            diagnosis=data.get("diagnosis"),
            recommendations=data.get("recommendations"),
            raw_text=data.get("raw_text")
        )

        # Study Results (optional)
        results = data.get("results", [])

        for r in results:
            StudyResultModel.create(
                study=study,
                key=r.get("key"),
                value=r.get("value"),
                unit=r.get("unit"),
                reference_range=r.get("reference_range")
            )

        return patient, study


def save_images_to_study(study, images):
    for img_path in images:
        StudyImageModel.create(
            study=study,
            url=img_path,
            description="Extracted from PDF"
        )


def upload_information(institution_id: int, file: UploadFile, user: user_schema.User):
    try:
        # Validate file
        if not file.filename or not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported."
            )

        # Save file
        try:
            file_path = save_file(file, institution_id)
        except Exception as e:
            logging.error(f"Error saving file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error saving file"
            )

        # Extract text
        try:
            text = extract_text_from_pdf(file_path)
            if not text or len(text.strip()) == 0:
                raise ValueError("Empty PDF text")
        except Exception as e:
            logging.error(f"Error extracting text: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from PDF"
            )

        # Call AI
        try:
            ai_result = call_llm(text)
        except QuotaExhaustedError as e:
            raise HTTPException(
                status_code=503,
                detail="AI service daily quota exceeded. Please try again tomorrow or contact support."
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail="AI processing failed")

        # Add raw text
        ai_result["raw_text"] = text

        # Save to DB
        try:
            patient, study = save_to_db_without_images(institution_id, ai_result, user)
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error saving data to database"
            )

        # Extract images
        try:
            images = extract_images_from_pdf(file_path, institution_id, patient.id, study.id)
        except Exception as e:
            logging.warning(f"Image extraction failed: {str(e)}")
            images = []  # not critical

        save_images_to_study(study, images)

        return {
            "message": "Study processed successfully",
            "images_extracted": len(images)
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logging.exception("Unexpected error in upload_information")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred"
        )


async def upload_information_bulk(
    institution_id: int,
    files: list[UploadFile],
    user: user_schema.User
):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    results = []
    errors = []

    async def process_file(file: UploadFile):
        async with semaphore:
            try:
                result = await run_in_threadpool(
                    upload_information,
                    institution_id,
                    file,
                    user
                )

                return {
                    "filename": file.filename,
                    "status": ResultEnum.SUCCESS.value,
                    "data": result
                }

            except HTTPException as e:
                return {
                    "filename": file.filename,
                    "status": ResultEnum.FAILURE.value,
                    "detail": e.detail
                }

            except Exception:
                logging.exception(f"Unexpected error processing {file.filename}")
                return {
                    "filename": file.filename,
                    "status": ResultEnum.FAILURE.value,
                    "detail": "Unexpected error"
                }

    tasks = [process_file(file) for file in files]

    responses = await asyncio.gather(*tasks)

    for r in responses:
        if r["status"] == ResultEnum.SUCCESS.value:
            results.append(r)
        else:
            errors.append(r)

    return {
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }
