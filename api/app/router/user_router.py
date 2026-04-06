import re
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from api.app.schema.user_creator_form_schema import UserCreateForm
from api.app.schema import user_schema
from api.app.service import user_service
from api.app.service import auth_service
from api.app.schema.token_schema import Token
from api.app.utils.input_validation import validate_name


router = APIRouter(
    tags=["users"]
)


@router.get("/health", tags=["Health"])
def healthcheck():
    """
    Health check endpoint.
    """
    return {"status": "API is up!"}


@router.get("/version", tags=["Info"])
def get_version():
    """
    Returns the current API version.
    """
    return {"version": "1.0.0"}


@router.post(
    "/user/",
    status_code=status.HTTP_201_CREATED,
    response_model=Token,
    summary="Create a new user"
)
def create_user(user_data: UserCreateForm = Depends(UserCreateForm.as_form)):
    """Create a new user with the provided details and upload an image.

    Args
        user_data (UserCreateForm): User data to create a new user.

    Returns:
        Token: Access tokens for the new user.
    """
    try:
        birthdate_parsed = datetime.fromisoformat(user_data.birthdate)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid birthdate format. Expected ISO format (YYYY-MM-DD)"
        )

    validate_name(user_data.username)

    try:
        user = user_schema.UserInput(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            name=user_data.name,
            last_name=user_data.last_name,
            birthdate=birthdate_parsed,
            country_id=user_data.country_id if user_data.country_id else None,  # Handle null country
            document_number=user_data.document_number,
            gender_id=user_data.gender_id if user_data.gender_id else None,
            institution=user_data.institution,
            role_id=user_data.role_id if user_data.role_id else None,
            contact_number=user_data.contact_number if user_data.contact_number else None
        )
    except ValidationError as e:
        logging.error(f"User data validation failed: {e.errors()}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {e.errors()}"
        )

    logging.info(f"Creating a new user in the database: {user.username}")
    try:
        new_user = user_service.create_user(user)
        response_data = user_service.create_tokens(new_user)

        logging.info(f"User {user.username} created successfully")
        return JSONResponse(
            content=response_data.model_dump(),
            status_code=status.HTTP_201_CREATED
        )

    except HTTPException as e:
        logging.error(f"User creation failed: {e.detail}")
        raise e

    except Exception as e:
        logging.error(f"Unexpected error during user creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during user creation"
        )


@router.post(
    "/login",
    tags=["users"],
    response_model=Token
)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login for access token.

    Args:
        form_data (OAuth2PasswordRequestForm, optional): Username/email or password.
        Defaults to Depends().

    Returns:
        Token: Access token and token type.
    """
    logging.info("Login user")

    # Authenticate the user
    user = auth_service.authenticate_user(form_data.username, form_data.password)

    # Generate both tokens
    response_data = user_service.create_tokens(user)

    return JSONResponse(content=response_data.model_dump(), status_code=status.HTTP_200_OK)
