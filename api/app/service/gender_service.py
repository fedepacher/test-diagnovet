import logging
from typing import List

from api.app.schema import gender_schema
from api.app.model.gender_model import Genders as GenderModel
from api.app.utils.functions import get_generic_list


def get_gender(accept_language: str) -> List[gender_schema.Gender]:
    """Get all the gender in the DB.

    Returns:
        list: List of gender.
    """
    logging.info("Getting all genders")
    return get_generic_list(name='gender', model=GenderModel, schema=gender_schema.Gender,
                            accept_language=accept_language)
