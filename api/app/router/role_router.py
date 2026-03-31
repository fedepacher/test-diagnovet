import logging
from fastapi import APIRouter, status, Request
from typing import List

from api.app.schema import role_schema
from api.app.service import role_service


router = APIRouter(prefix="/role")


@router.get(
    "/",
    tags=["roles"],
    status_code=status.HTTP_200_OK,
    response_model=List[role_schema.RolesBase]
)
def get_prole_list(request: Request) -> list:
    """
    Get all DB roles.

    Returns:
        list: A list containing all the roles.
    """
    logging.info("Getting roles")
    accept_language = request.state.accept_language
    role = role_service.get_roles(accept_language)
    return role
