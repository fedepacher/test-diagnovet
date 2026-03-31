import logging
from fastapi import APIRouter, status, Request
from typing import List

from api.app.schema import breed_schema
from api.app.service import breed_service


router = APIRouter(prefix="/breed")


@router.get(
    "/",
    tags=["breed"],
    status_code=status.HTTP_200_OK,
    response_model=List[breed_schema.Breed]
)
def get_breed_list(request: Request) -> list:
    """
    Get all DB breeds.

    Returns:
        list: A list containing all the breed.
    """
    accept_language = request.state.accept_language
    logging.info(f"get_breed_list(accept_language: {accept_language}")
    breed = breed_service.get_breeds(accept_language)
    return breed
