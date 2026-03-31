import logging
from fastapi import APIRouter, Depends, status, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import ValidationError

from api.app.service import profile_service
from api.app.schema.user_schema import User
from api.app.schema import profile_schema
from api.app.service.auth_service import get_current_user


router = APIRouter(prefix="/profile")


@router.get(
    "/",
    tags=["profile"],
    status_code=status.HTTP_200_OK,
    response_model=profile_schema.ProfileResponse,
    description="This endpoint get the user's profile."
)
def get_profile_info(request: Request, current_user: User = Depends(get_current_user)):
    """
    Get profile information.

    Args:
        request (Request): Request object.
        current_user (User): User object.

    Returns:
        JSON: JSON containing profile, user and institution information.
    """
    logging.info("Getting profile information")
    accept_language = request.state.accept_language
    profile_info = profile_service.get_profile_info(current_user, accept_language)
    return profile_info


@router.patch(
    "/",
    tags=["profile"],
    status_code=status.HTTP_200_OK,
    response_model=profile_schema.ProfileOut,
    summary="Update user profile",
    description="Update the current user's profile information."
)
def update_profile(
        request: Request,
        email: Optional[str] = Form(None, description="The profile's email address."),
        name: Optional[str] = Form(None, description="The profile's first name."),
        last_name: Optional[str] = Form(None, description="The profile's last name."),
        document_number: Optional[str] = Form(None, description="The profile's document number."),
        contact_number: str = Form(None, description="The profile's contact number."),
        birthdate: Optional[str] = Form(None, description="The profile's birthdate in ISO format (YYYY-MM-DD)."),
        gender_id: Optional[int] = Form(None, description="The profile's gender id."),
        country_id: Optional[int] = Form(None, description="The profile's country id."),
        role_id: Optional[int] = Form(None, description="The user's role."),
        current_user: User = Depends(get_current_user)
        ):
    """
    Update profile record in the database.

    Args:
        request (Request): Language.
        email (str): The Profile's email address.
        name (str): The Profile's first name.
        last_name (str): The Profile's last name.
        document_number (str): The Profile's document number.
        contact_number (str): The Profile's contact number.'
        birthdate (str): The Profile's birthdate in ISO format (YYYY-MM-DD).
        gender_id (str): The Profile's gender id.
        country_id (str): The Profile's country id.
        role_id (int): User role.
        current_user (User): The currently authenticated user, retrieved via dependency injection.

    Returns:
        dict: A dictionary containing the Profile created information.
    """
    try:
        updated_data = profile_schema.ProfileIn(
                    email=email,
                    name=name,
                    last_name=last_name,
                    document_number=document_number,
                    contact_number=contact_number,
                    birthdate=birthdate,
                    gender_id=gender_id,
                    country_id=country_id,
                    role_id=role_id
                )
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    logging.info("Updating profile")
    accept_language = request.state.accept_language
    updated_profile = profile_service.update_profile(updated_data, current_user, accept_language)
    return updated_profile
