import logging
from fastapi import APIRouter, Depends, Request, status

from api.app.schema import study_schema, user_schema
from api.app.service import study_service
from api.app.service.auth_service import get_current_user
from api.app.utils.decorators import paginate, fetch_institution


router = APIRouter(prefix="/study")


@router.get(
    "/",
    tags=["study"],
    status_code=status.HTTP_200_OK,
    response_model=study_schema.PaginatedStudiesResponse
)
@fetch_institution()
@paginate(study_schema.PaginatedStudiesResponse)
async def get_all_study_for_patient(
        institution_id: int,
        patient_id: int,
        current_user: user_schema.User = Depends(get_current_user)
):
    """
    Get all DB studies.

    Args:
        institution_id (int): The institution ID.
        patient_id (int): The patient ID.
        current_user (user_schema.User): The current user.

    Returns:
        list: A list containing all the study.
    """
    logging.info(f"Get studies for patient {patient_id}")
    studies = await study_service.get_all_studies(institution_id=institution_id,
                                                  patient_id=patient_id)
    return studies


@router.get(
    "/results/",
    tags=["study"],
    status_code=status.HTTP_200_OK,
    response_model=study_schema.StudyDetailSchema
)
@fetch_institution()
async def get_study_result_by_id(
        request: Request,
        institution_id: int,
        result_id: int,
        current_user: user_schema.User = Depends(get_current_user)
):
    """
    Get study result by id.

    Args:
        request (Request): The incoming request.
        institution_id (int): The institution ID.
        result_id (int): The result ID.
        current_user (user_schema.User): The current user.

    Returns:
        list: A list containing all the results.
    """
    logging.info(f"Get studies result {result_id}")
    accept_language = request.state.accept_language
    studies = await study_service.get_study_result(institution_id=institution_id,
                                                   result_id=result_id,
                                                   accept_language=accept_language)
    return studies
