import logging
from typing import List

from api.app.schema import country_schema
from api.app.model.country_model import Countries as CountryModel
from api.app.utils.functions import get_generic_list


def get_countries(accept_language: str) -> List[country_schema.Country]:
    """Get all the countries in the DB.

    Returns:
        list: List of countries.
    """
    logging.info("Getting all countries")
    return get_generic_list(name='country', model=CountryModel, schema=country_schema.Country,
                            accept_language=accept_language)
