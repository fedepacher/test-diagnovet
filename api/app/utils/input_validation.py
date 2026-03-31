""" Input validation parameter functions """
import re
from fastapi import HTTPException

from api.app.model.user_institution_model import UsersInstitutions


VALID_NAME_PATTERN = r"^[\w\s\-\.,&()áéíóúÁÉÍÓÚñÑ']+$"
MAX_CHAR_LENGTH = 100


def validate_name(
        name: str,
        length: int = MAX_CHAR_LENGTH,
        string_pattern: str = VALID_NAME_PATTERN
) -> None:
    """
    Validates that the institution name is not empty, under 50 characters,
    and only contains allowed characters.

    Args:
        name (str): Institution name to validate.
        length (int, optional): Length of institution name to validate.
        string_pattern (str, optional): String pattern to validate against.

    Raises:
        ValueError: If the name is empty or contains invalid characters.
    """
    regex_pattern = re.compile(string_pattern)
    if not name or not name.strip():
        raise ValueError("Name cannot be empty.")

    if len(name.strip()) >= length:
        raise ValueError(F"Name must be less than {length} characters.")

    if not regex_pattern.fullmatch(name):
        raise ValueError("Name contains invalid characters.")


def validate_institution(institution_id: int, user_id: int):
    """
    Validates that the institution ID is valid.

    Args:
        institution_id (int): Institution ID to validate.
        user_id (int): User ID to validate.

    Raises:
        ValueError: If the institution ID is invalid.
    """
    relation = (
        UsersInstitutions
        .select()
        .where(
            (UsersInstitutions.user == user_id) &
            (UsersInstitutions.institution == institution_id) &
            (UsersInstitutions.active == True) &
            (UsersInstitutions.deleted_at.is_null())
        )
        .exists()
    )
    if not relation:
        raise HTTPException(
            status_code=403,
            detail=f"Institution {institution_id} does not belong to user {user_id}"
        )
