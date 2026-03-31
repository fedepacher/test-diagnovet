import logging
from typing import List

from api.app.schema import role_schema
from api.app.model.role_model import Roles as RoleModel
from api.app.utils.functions import get_generic_list


def get_roles(accept_language: str) -> List[role_schema.RolesBase]:
    """Get all the countries in the DB.

    Returns:
        list: List of countries.
    """
    logging.info("Getting all countries")
    return get_generic_list(name='role', model=RoleModel,
                            schema=role_schema.RolesBase,
                            accept_language=accept_language)
