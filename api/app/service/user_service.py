import logging
from datetime import datetime
from fastapi import HTTPException, status
from peewee import fn

from api.app.model.country_model import Countries as CountryModel
from api.app.model.gender_model import Genders as GenderModel
from api.app.model.institution_model import Institutions as InstitutionModel
from api.app.model.role_model import Roles as RolesModel
from api.app.model.profile_model import Profiles as ProfileModel
from api.app.model.user_model import Users as UserModel
from api.app.model.user_institution_model import UsersInstitutions as UserInstitutionModel
from api.app.schema import user_schema
from api.app.schema.token_schema import Token
from api.app.service.auth_service import generate_access_token, get_password_hash
from api.app.utils.functions import check_if_id_exist
from api.app.utils.global_def import StatusEnum
from api.app.utils.db import db


def create_user(user: user_schema.UserInput) -> user_schema.User:
    """Create users and store them in the DB.

    Args:
        user (user_schema.UserInput): User parameters.

    Raises:
        HTTPException: If the user is already created or validation fails.

    Returns:
        UserBaseRegistered: Created user instance.
    """
    logging.info(f"Creating user: {user.username}")
    username_lower = user.username.lower()
    email_lower = str(user.email).lower()
    # Check if email and username exits
    current_user = UserModel.filter(
        (fn.LOWER(UserModel.email) == email_lower) |
        (fn.LOWER(UserModel.username) == username_lower)
    ).first()
    if current_user:
        msg = "Email already registered"
        if current_user.username.lower() == username_lower:
            msg = "Username already registered"
        logging.debug(msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    db_institution = InstitutionModel.filter((fn.LOWER(InstitutionModel.name) == user.institution)).first()

    gender_id = None
    country_id = None
    role_id = None

    if user.gender_id is not None:
        check_if_id_exist(user.gender_id, GenderModel)
        gender_id = user.gender_id

    if user.country_id is not None:
        check_if_id_exist(user.country_id, CountryModel)
        country_id = user.country_id

    if user.role_id is not None:
        check_if_id_exist(user.role_id, RolesModel)
        role_id = user.role_id

    with db.atomic():

        db_profile = ProfileModel(
            email=user.email,
            name=user.name,
            last_name=user.last_name,
            document_number=user.document_number,
            contact_number=user.contact_number,
            birthdate=user.birthdate,
            gender=gender_id,
            country=country_id,
            updated_at=datetime.now(),
            created_at=datetime.now(),
            updated_by=None,
            created_by=0,
            role=role_id
        )
        logging.info(f"Saving user profile: {user.username} in profiles table")
        db_profile.save()

        db_user = UserModel(
            profile=db_profile.id,
            username=user.username,
            email=user.email,
            password=get_password_hash(user.password),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deleted_at=None,
            active=True,
            status=StatusEnum.ACTIVE
        )
        logging.info(f"Saving user: {user.username} in users table")
        db_user.save()

        if not db_institution:
            db_institution = InstitutionModel(
                name=user.institution.lower(),
                updated_at=datetime.now(),
                created_at=datetime.now(),
                updated_by=db_user.id,
                created_by=db_user.id,
                active=True,
                status=StatusEnum.ACTIVE
            )
            logging.info(f"Saving institution: {user.institution} in institutions table")
            db_institution.save()

        db_user_institution = UserInstitutionModel(
            institution=db_institution.id,
            user=db_user.id,
            updated_by=db_user.id,
            created_by=db_user.id,
            active=True,
            status=StatusEnum.ACTIVE
        )
        logging.info(f"Creating user-institution relationship for user: {user.username}")
        db_user_institution.save()

    logging.info(f"User {user.username} was successfully created with all relationships")

    user_ret = user_schema.User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
    )
    return user_ret


def create_tokens(user: user_schema.User) -> Token:
    # Generate new access and refresh tokens
    access_token = generate_access_token(user)

    # Return both tokens in the response
    response_data = Token(
        access_token=access_token,
        token_type="bearer"
    )

    return response_data
