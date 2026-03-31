import logging
from typing import List

from api.app.schema import breed_schema
from api.app.model.breed_model import Breeds as BreedModel
from api.app.utils.functions import get_generic_list


def get_breeds(accept_language: str) -> List[breed_schema.Breed]:
    """Get all the breeds in the DB.

    Returns:
        list: List of breeds.
    """
    logging.info("Getting all breeds")
    return get_generic_list(name='breed', model=BreedModel, schema=breed_schema.Breed,
                            accept_language=accept_language)
