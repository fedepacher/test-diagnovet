""" API endpoints to handle institutions. """

import logging
from fastapi import APIRouter, Depends, Form, Query, status

from api.app.schema.institution_schema import InstitutionResponse
from api.app.schema.user_schema import User
from api.app.service.auth_service import get_current_user
from api.app.service.institution_service import update_institution


router = APIRouter(prefix="/institution", tags=["institution"])


@router.patch(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Update institution name",
    description="""
        This endpoint update the institution name for the specific user. 
    """,
    response_model=InstitutionResponse,
    responses={
            status.HTTP_200_OK: {
                "description": "Update institution name processed successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 4,
                            "status": "success"
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Validation error, institution not found",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "Institution not found or not accessible."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Internal server error while processing the webhook",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "Name contains invalid characters."
                        }
                    }
                }
            }
        }
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
    response = update_institution(institution_id, name, current_user)
    return response
