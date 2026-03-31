import logging
from fastapi import HTTPException, status

from api.app.model.institution_model import Institutions as InstitutionModel
from api.app.schema import institution_schema, user_schema
from api.app.utils.global_def import ResultEnum, StatusEnum
from api.app.utils.input_validation import validate_name


def update_institution(
        institution_id: int,
        name: str,
        user: user_schema.User) -> institution_schema.InstitutionResponse:
    """
    Update institution name.

    Args:
        institution_id (int): Institution ID.
        name (str): Institution name.
        user (User): Current user. Defaults to Depends(get_current_user).

    Returns:
        InstitutionResponse: Updated institution response.

    Raises:
        HTTPException: If the name is invalid or institution not found/accessible.
    """
    logging.info(f"Update institution {institution_id} name to '{name}' by user {user.id}")

    validate_name(name=name)

    institution = InstitutionModel.get_or_none(
        (InstitutionModel.id == institution_id) &
        (InstitutionModel.deleted_at.is_null()) &
        (InstitutionModel.active == True) &
        (InstitutionModel.status == StatusEnum.ACTIVE)
    )
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found or not accessible."
        )

    institution.name = name
    institution.updated_by = user.id
    institution.save()

    return institution_schema.InstitutionResponse(
        id=institution.id,
        status=ResultEnum.SUCCESS
    )
