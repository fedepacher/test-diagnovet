from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel

from api.app.schema import user_schema
from api.app.schema import institution_schema, gender_schema, country_schema, role_schema


class ProfileRaw(BaseModel):
    """Base profile schema with optional fields properly defined."""
    contact_email: Optional[str] = None
    name: Optional[str] = None
    last_name: Optional[str] = None
    document_number: Optional[str] = None
    contact_number: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileBase(BaseModel):
    """Base profile schema with optional fields properly defined."""
    contact_email: Optional[str] = None
    name: Optional[str] = None
    last_name: Optional[str] = None
    document_number: Optional[str] = None
    contact_number: Optional[str] = None
    birthdate: Optional[date] = None
    gender: Optional[gender_schema.Gender] = None
    country: Optional[country_schema.Country] = None

    class Config:
        from_attributes = True


class Profile(ProfileBase):
    """Extended profile schema with relationship fields."""
    role: Optional[role_schema.RolesBase] = None


class ProfileResponse(BaseModel):
    profile: Profile
    user: user_schema.UserProfile
    institutions: institution_schema.Institution

    class Config:
        from_attributes = True


class ProfileIn(BaseModel):
    """Input schema for profile updates with all optional fields."""
    email: Optional[str] = None
    role_id: Optional[int] = None
    name: Optional[str] = None
    last_name: Optional[str] = None
    document_number: Optional[str] = None
    contact_number: Optional[str] = None
    birthdate: Optional[date] = None
    gender_id: Optional[int] = None
    country_id: Optional[int] = None

    class Config:
        from_attributes = True

class ProfileOut(BaseModel):
    msg: str
