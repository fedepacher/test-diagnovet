import logging
from fastapi import HTTPException, status

from api.app.model.country_model import Countries as CountryModel
from api.app.model.gender_model import Genders as GenderModel
from api.app.model.institution_model import Institutions as InstitutionModel
from api.app.model.role_model import Roles as RolesModel
from api.app.model.profile_model import Profiles as ProfileModel
from api.app.model.user_model import Users as UserModel
from api.app.model.user_institution_model import UsersInstitutions as UserInstitutionModel
from api.app.schema import (country_schema, gender_schema, institution_schema, role_schema, profile_schema,
                            user_schema)
from api.app.utils.functions import get_language_fields


def get_profile_info(user: user_schema.User, accept_language: str) -> profile_schema.ProfileResponse | None:
    """Get user information in the DB.

        Args:
            user (user_schema.User): User.
            accept_language (str): Language.

        Returns:
            JSON: Profile information, User information and Institution information of the user.
        """
    logging.info(f"Loading profile information for user: {user.username}")
    try:
        language_fields = get_language_fields(accept_language)
        user_data = (
            UserModel
            .select(
                UserModel.username,
                UserModel.email.alias('email'),
                UserModel.created_at,
                UserModel.updated_at,
                UserModel.active,
                UserModel.status,
                RolesModel.id.alias('role_id'),
                language_fields['role'].alias('role_name'),
                ProfileModel.email.alias('contact_email'),
                ProfileModel.name,
                ProfileModel.last_name,
                ProfileModel.document_number,
                ProfileModel.contact_number,
                ProfileModel.birthdate,
                GenderModel.id.alias('gender_id'),
                language_fields["gender"].alias('gender_name'),
                CountryModel.id.alias('country_id'),
                language_fields["country"].alias('country_name'),
                ProfileModel.created_at.alias('profile_created_at'),
                ProfileModel.updated_at.alias('profile_updated_at')
            )
            .join(ProfileModel, on=(UserModel.profile == ProfileModel.id))
            .left_outer_join(RolesModel, on=(ProfileModel.role == RolesModel.id))
            .left_outer_join(GenderModel, on=(ProfileModel.gender == GenderModel.id))
            .left_outer_join(CountryModel, on=(ProfileModel.country == CountryModel.id))
            .where(UserModel.id == user.id)
            .dicts()
            .get()
        )

        if not user_data:
            logging.info(f"Profile for {user.email} does not exist.")
            return None

        logging.info(f"Profile for {user.email} exists.")

        institution = (
            InstitutionModel
            .select(
                InstitutionModel.id.alias('institution_id'),
                InstitutionModel.name.alias('institution_name'),
                InstitutionModel.active.alias('institution_active'),
                InstitutionModel.status.alias('institution_status'),
                InstitutionModel.created_at.alias('created_at'),
                InstitutionModel.updated_at.alias('updated_at'),
                InstitutionModel.deleted_at.alias('deleted_at'),
                InstitutionModel.created_by.alias('created_by'),
                InstitutionModel.updated_by.alias('updated_by'),
                InstitutionModel.deleted_by.alias('deleted_by'),
            )
            .join(UserInstitutionModel)
            .where(
                (UserInstitutionModel.user == user.id) &
                (UserInstitutionModel.active == True)
            )
            .dicts()
            .get()
        )

        new_institution = institution_schema.Institution(
            id=institution['institution_id'],
            name=institution['institution_name'],
            active=institution['institution_active'],
            status=institution['institution_status'],
            created_at=institution['created_at'],
            updated_at=institution['updated_at'],
            deleted_at=institution['deleted_at'],
            created_by=institution['created_by'],
            updated_by=institution['updated_by'],
            deleted_by=institution['deleted_by'],
        )

        gender_obj = None
        if user_data['gender_id'] is not None:
            gender_obj = gender_schema.Gender(
                id=user_data['gender_id'],
                name=user_data['gender_name']
            )

        country_obj = None
        if user_data['country_id'] is not None:
            country_obj = country_schema.Country(
                id=user_data['country_id'],
                name=user_data['country_name']
            )

        role_obj = None
        if user_data['role_id'] is not None:
            role_obj = role_schema.RolesBase(
                id=user_data['role_id'],
                name=user_data['role_name'],
            )

        new_profile = profile_schema.ProfileResponse(
            profile=profile_schema.Profile(
                contact_email=user_data['contact_email'],
                name=user_data['name'],
                last_name=user_data['last_name'],
                document_number=user_data['document_number'],
                contact_number=user_data['contact_number'],
                birthdate=user_data['birthdate'],
                gender=gender_obj,
                country=country_obj,
                created_at=user_data['profile_created_at'],
                updated_at=user_data['profile_updated_at'],
                role=role_obj
            ),
            user=user_schema.UserProfile(
                username=user_data['username'],
                email=user_data['email'],
                created_at=user_data['created_at'],
                updated_at=user_data['updated_at'],
                active=user_data['active'],
                status=user_data['status']
            ),
            institutions=new_institution
        )
        return new_profile

    except HTTPException as e:
        logging.error(f"HTTPException occurred: {e.detail}")
        raise e

    except Exception as e:
        logging.error(f"An error occurred while loading profile information: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the request"
        )
