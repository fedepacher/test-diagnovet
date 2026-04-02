""" API endpoints to handle institutions. """

import logging
from fastapi import APIRouter, Depends, Form, HTTPException, status, Query
from typing import List

from api.app.schema.institution_schema import InstitutionBase, InstitutionResponse
from api.app.schema.user_schema import User
from api.app.service.auth_service import get_current_user
from api.app.service import institution_service


router = APIRouter(prefix="/institution", tags=["institution"])


@router.post(
    "/",
    tags=["patient"],
    status_code=status.HTTP_201_CREATED,
    response_model=InstitutionResponse,
)
def create_institution(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new institution record in the database.

    Args:
        name: Institution name
        current_user: Authenticated user

    Returns:
        InstitutionBase: Created institution ID and name
    """
    return institution_service.create_institution(
        name=name,
        user=current_user,
    )


@router.get(
    "/all",
    tags=["patient"],
    status_code=status.HTTP_200_OK,
    response_model=List[InstitutionBase]
)
async def get_all_institutions():
    """
    Retrieve all institution.

    Returns:
        patient_schema.PaginatedPatientsResponse: A paginated response containing the list of patients.
    """
    logging.info("Getting all institutions")

    institution = institution_service.get_institutions()

    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No institutions found."
        )

    return institution


@router.get(
    "/",
    tags=["patient"],
    status_code=status.HTTP_200_OK,
    response_model=List[InstitutionBase]
)
async def get_all_institutions_by_user(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all institution associated with the authenticated user.

    Args:
        current_user (User): The currently authenticated user.

    Returns:
        patient_schema.PaginatedPatientsResponse: A paginated response containing the list of patients.
    """
    logging.info(f"Getting institutions for user {current_user.username}")

    institution = institution_service.get_institutions_by_user(current_user)

    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No institution found for the user {current_user.username}."
        )

    return institution



@router.patch(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Update institution name",
    description="""
        This endpoint update the institution name for the specific user. 
    """,
    response_model=InstitutionResponse,
)
def update_institution_name(
        institution_id: int = Query(..., gt=0),
        name: str = Form(..., description="Institution name"),
        current_user: User = Depends(get_current_user),
    ):
    """
    Update institution name.

    Args:
        institution_id (int): Institution ID.
        name (str): Institution name.
        current_user (User, optional): Current user. Defaults to Depends(get_current_user).

    Returns:
        InstitutionResponse: Institution response.
    """
    logging.info("Update institution name")
    response = institution_service.update_institution(institution_id, name, current_user)
    return response
