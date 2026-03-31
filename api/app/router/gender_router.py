import logging
from fastapi import APIRouter, status, Request
from typing import List

from api.app.schema import gender_schema
from api.app.service import gender_service


router = APIRouter(prefix="/gender")


@router.get(
    "/",
    tags=["gender"],
    status_code=status.HTTP_200_OK,
    response_model=List[gender_schema.Gender]
)
def get_gender_list(request: Request):
    """
    Get all DB gender.

    Returns:
        list: A list containing all the gender.
    """
    logging.info("Getting gender")
    accept_language = request.state.accept_language
    gender = gender_service.get_gender(accept_language)
    return gender
