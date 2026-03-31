import logging
from typing import List

from api.app.schema import specie_schema
from api.app.model.specie_model import Species as SpecieModel
from api.app.utils.functions import get_generic_list


def get_species(accept_language: str) -> List[specie_schema.Specie]:
    """Get all the species in the DB.

    Returns:
        list: List of species.
    """
    logging.info("Getting all species")
    return get_generic_list(name='specie', model=SpecieModel, schema=specie_schema.Specie,
                            accept_language=accept_language)
