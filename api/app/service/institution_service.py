import logging
from datetime import datetime
from fastapi import HTTPException, status
from peewee import fn
from typing import List

from api.app.model.institution_model import Institutions as InstitutionModel
from api.app.model.user_institution_model import UsersInstitutions as UsersInstitutionsModel
from api.app.schema import institution_schema, user_schema
from api.app.utils.global_def import ResultEnum, StatusEnum
from api.app.utils.input_validation import validate_name
from api.app.utils.db import db


def create_institution(
    name: str,
    user: user_schema.User
) -> institution_schema.InstitutionResponse:
    """
    Create a new institution and link it to the user.
    If institution already exists, just create the relationship (if not exists).
    """

    logging.info(f"Creating institution '{name}' for user {user.username}")

    try:
        with db.atomic():
            normalized_name = name.strip().lower()

            # Check if institution already exists (case insensitive)
            institution = (
                InstitutionModel
                .select()
                .where(fn.LOWER(InstitutionModel.name) == normalized_name)
                .first()
            )

            # Create if not exists
            if not institution:
                logging.info(f"Institution '{name}' does not exist. Creating new one.")

                institution = InstitutionModel.create(
                    name=name.strip(),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by=user.id,
                    updated_by=user.id,
                    active=True,
                    status=StatusEnum.ACTIVE
                )
            else:
                logging.info(f"Institution '{name}' already exists (id={institution.id})")

            # Check if relation already exists
            relation_exists = (
                UsersInstitutionsModel
                .select()
                .where(
                    (UsersInstitutionsModel.user == user.id) &
                    (UsersInstitutionsModel.institution == institution.id) &
                    (UsersInstitutionsModel.deleted_at.is_null(True))
                )
                .exists()
            )

            # Create relation if not exists
            if not relation_exists:
                logging.info(f"Linking user {user.username} with institution {institution.name}")

                UsersInstitutionsModel.create(
                    user=user.id,
                    institution=institution.id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by=user.id,
                    updated_by=user.id,
                    active=True,
                    status=StatusEnum.ACTIVE
                )
            else:
                logging.info("User already linked to this institution")

            # Return response
            return institution_schema.InstitutionResponse(
                id=institution.id,
                status=ResultEnum.SUCCESS
            )

    except Exception as e:
        logging.error(f"Error creating institution: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating institution"
        )


def get_institutions()-> List[institution_schema.InstitutionBase]:
    """
    Get all institutions.

    Returns:
        InstitutionBase: Institution information.
    """
    logging.info("Getting all institutions")

    try:
        query = (
            InstitutionModel
            .select(
                InstitutionModel.id,
                InstitutionModel.name
            )
            .where(
                (InstitutionModel.active == True) &
                (InstitutionModel.deleted_at.is_null(True))
            )
            .order_by(InstitutionModel.name.asc())
        )

        institutions = [
            institution_schema.InstitutionBase(
                id=row.id,
                name=row.name
            )
            for row in query
        ]

        return institutions

    except Exception as e:
        logging.error(f"Error retrieving all institutions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving all institutions"
        )


def get_institutions_by_user(
    user: user_schema.User
) -> List[institution_schema.InstitutionBase]:
    """
    Retrieves institutions for a user

    Args:
        user (User): Current user. Defaults to Depends(get_current_user).

    Returns:
        InstitutionBase: Institution information.
    """
    logging.info(f"Getting institutions for user {user.username}")

    try:
        query = (
            InstitutionModel
            .select(
                InstitutionModel.id,
                InstitutionModel.name
            )
            .join(
                UsersInstitutionsModel,
                on=(UsersInstitutionsModel.institution == InstitutionModel.id)
            )
            .where(
                (UsersInstitutionsModel.user == user.id) &
                (UsersInstitutionsModel.active == True) &
                (UsersInstitutionsModel.deleted_at.is_null(True)) &
                (InstitutionModel.active == True) &
                (InstitutionModel.deleted_at.is_null(True))
            )
        )

        institutions = [
            institution_schema.InstitutionBase(
                id=row.id,
                name=row.name
            )
            for row in query
        ]

        return institutions

    except Exception as e:
        logging.error(f"Error retrieving institutions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving institutions"
        )


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
