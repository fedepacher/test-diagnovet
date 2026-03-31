import logging
from fastapi import APIRouter, status, Request
from typing import List

from api.app.schema import specie_schema
from api.app.service import specie_service


router = APIRouter(prefix="/specie")


@router.get(
    "/",
    tags=["specie"],
    status_code=status.HTTP_200_OK,
    response_model=List[specie_schema.Specie]
)
def get_specie_list(request: Request) -> list:
    """
    Get all DB species.

    Returns:
        list: A list containing all the species.
    """
    accept_language = request.state.accept_language
    logging.info(f"get_specie_list(accept_language: {accept_language}")
    specie = specie_service.get_species(accept_language)
    return specie