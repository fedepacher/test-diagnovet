from datetime import date
from fastapi import HTTPException, status

from api.app.utils.functions import check_if_id_exist
from api.app.model.country_model import Countries as CountryModel
from api.app.model.gender_model import Genders as GenderModel


def parse_birthdate(birthdate: str) -> date:
    """
    Parse birthdate string into date object.

    Args:
        birthdate (str): Date string in YYYY-MM-DD format

    Returns:
        date: Parsed date object

    Raises:
        HTTPException: If date format is invalid
    """
    try:
        return date.fromisoformat(birthdate)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Expected ISO format (YYYY-MM-DD)"
        )


def validate_required_patient_fields(email: str, name: str, last_name: str):
    """
    Validate required fields for patient creation/update.
    
    Args:
        email (str): Patient email
        name (str): Patient name
        last_name (str): Patient last name
        
    Raises:
        HTTPException: If any required field is missing
    """
    if not email or not name or not last_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email, name, and last_name are required fields"
        )


def validate_country_id_required(country_id):
    """
    Validate that country_id is provided for patient creation.

    Args:
        country_id (int): Country ID to validate

    Raises:
        HTTPException: If country_id is None or invalid
    """
    if country_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="country_id is required for patient creation"
        )


def validate_patient_foreign_keys(country_id=None, gender_id=None):
    """
    Validate foreign key references for patient data.

    Only validates non-None values, allowing optional fields.

    Args:
        country_id (int, optional): Country ID (optional)
        gender_id (int, optional): Gender ID (optional)

    Raises:
        HTTPException: If any provided ID doesn't exist in database
    """
    if country_id is not None:
        check_if_id_exist(country_id, CountryModel)
    if gender_id is not None:
        check_if_id_exist(gender_id, GenderModel)
