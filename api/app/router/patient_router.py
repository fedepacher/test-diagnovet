import logging
from fastapi import APIRouter, Body, Depends, status, Path, UploadFile, Request
from typing import List, Optional

from api.app.schema import patient_schema
from api.app.service import patient_service
from api.app.schema.user_schema import User
from api.app.service.auth_service import get_current_user
from api.app.utils.decorators import paginate, fetch_institution


router = APIRouter(prefix="/patient")


@router.post(
    "/",
    tags=["patient"],
    status_code=status.HTTP_201_CREATED,
    response_model=patient_schema.PatientResponse,
    summary="Create a new patient with profile and initial status",
    description="Creates a new patient record including profile information and initial status data."
)
@fetch_institution()
async def create_patient(
    institution_id: int,
    data: patient_schema.PatientCreateRaw,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new patient record in the database.

    Args:
        institution_id: Institution ID
        data: Patient personal and information
        current_user: Authenticated user

    Returns:
        PatientResponse: Created patient ID and operation status

    Raises:
        HTTPException 400: Invalid data or duplicate email
        HTTPException 404: Referenced entities not found
        HTTPException 500: Server error during creation
    """
    return await patient_service.create_patient_from_scratch(
        institution_id=institution_id,
        data=data,
        user=current_user
    )


@router.get(
    "/",
    tags=["patient"],
    status_code=status.HTTP_200_OK,
    response_model=patient_schema.PaginatedPatientsResponse
)
@fetch_institution()
@paginate(patient_schema.PaginatedPatientsResponse)
async def get_all_patients(
    request: Request,
    institution_id: int,
    name: Optional[str] = '',
    order_by: Optional[str] = '',
    order_dir: Optional[str] = '',
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all patients associated with the authenticated user.

    Args:
        request (Request): The incoming request.
        current_user (User): The currently authenticated user.
        institution_id (Optional[int]): ID of the institution to filter patients. Defaults to 0 (no filter).
        name (Optional[str]): Patient's name.
        order_by (str): Order fields according to the given order.
        order_dir (str): Order fields asc or desc.
        page (int): Page number for pagination.
        limit (int): Maximum number of patients to retrieve per page.

    Returns:
        patient_schema.PaginatedPatientsResponse: A paginated response containing the list of patients.
    """
    logging.info(f"Getting patients for user {current_user.username} with filters: institution_id={institution_id}")

    accept_language = request.state.accept_language
    patients = await patient_service.get_patients(
        current_user,
        institution_id=institution_id,
        name=name,
        accept_language=accept_language,
        order_by=order_by,
        order_dir=order_dir
    )

    return patients


@router.get(
    "/{patient_id}",
    tags=["patient"],
    status_code=status.HTTP_200_OK,
    response_model=patient_schema.PatientBasicData,
    summary="Get patient by ID",
    description="Retrieve complete patient information including profile, current status, and sports data"
)
@fetch_institution()
async def get_patient_by_id(
    request: Request,
    institution_id: int,
    patient_id: int = Path(
        ...,
        description="Unique identifier of the patient",
        example=1,
        gt=0
    ),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve patient information by ID.

    Returns complete patient data including personal information, current status,
    and sports-related data. The response type depends on data availability:

    - PatientId: When only basic patient ID is accessible (limited permissions)
    - Patient: Complete patient information with all related data

    Args:
        request (Request): HTTP request containing language preferences
        institution_id (int): ID of the institution to filter patients..
        patient_id (int): Unique identifier of the patient to retrieve
        current_user (User): Authenticated user making the request

    Returns:
        patient_schema.PatientBasicData: Basic ID info of the patient data

    Raises:
        HTTPException 404: Patient not found or not accessible to user
        HTTPException 500: Server error during data retrieval
    """
    return patient_service.get_patient(
        patient_id=patient_id,
        institution_id=institution_id,
        user=current_user,
        accept_language=request.state.accept_language
    )


@router.post(
    "/upload_patient",
    status_code=status.HTTP_201_CREATED,
    summary="Load patients from PDF file",
    description="Load patients from PDF file."
)
@fetch_institution()
async def upload_patients_pdf(
        institution_id: int,
        files: List[UploadFile],
        current_user: User = Depends(get_current_user)):
    """
    Upload a PDF with patient data and load it into the database.
    The 'birthdate' field is transformed to ISO format.

    Args:
        institution_id (int): Institution ID.
        files (List): PDF files list with patient data.
        current_user: Authenticated user.
    """
    return await patient_service.upload_information_bulk(
        institution_id,
        files,
        current_user
    )
