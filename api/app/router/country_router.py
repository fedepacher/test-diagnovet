import logging
from fastapi import APIRouter, status, Request
from typing import List

from api.app.schema import country_schema
from api.app.service import country_service


router = APIRouter(prefix="/country")


@router.get(
    "/",
    tags=["country"],
    status_code=status.HTTP_200_OK,
    response_model=List[country_schema.Country]
)
def get_country_list(request: Request) -> list:
    """
    Get all DB countries.

    Returns:
        list: A list containing all the countries.
    """
    accept_language = request.state.accept_language
    logging.info(f"get_country_list(accept_language: {accept_language}")
    country = country_service.get_countries(accept_language)
    return country
