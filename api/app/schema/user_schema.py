from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from api.app.schema import country_schema, gender_schema, institution_schema, role_schema


class UserBase(BaseModel):
    """User base class.

    Args:
        BaseModel (_type_): BaseModel checker.
    """
    name: str = Field(..., max_length=50, example='Alejandro')
    last_name: str = Field(..., max_length=50, example='Estocolmo')
    birthdate: date = Field(..., default_factory=date.today)
    country: Optional[country_schema.Country] = None
    document_number: str = Field(..., max_length=50, example='111111111')
    gender: Optional[gender_schema.Gender] = None
    contact_number: Optional[str] = Field(None, max_length=50, example='111111111')

    class Config:
        from_attributes = True


class UserBaseRegistered(BaseModel):
    """User base class.

    Args:
        BaseModel (_type_): BaseModel checker.
    """
    email: EmailStr = Field(..., example='myemail@mail.com')
    username: str = Field(..., min_length=3, max_length=50, example='myusername')

    class Config:
        from_attributes = True


class User(UserBaseRegistered):
    """User class.

    Args:
        UserBase (_type_): BaseModel checker.
    """
    id: int = Field(..., example='5')


class UserSensitiveInformation(BaseModel):
    """User sensitive information.

    Args:
        BaseModel (_type_): BaseModel checker.
    """
    password: str = Field(..., min_length=8, max_length=64, example='mypassword')


class UserRegister(UserBase, UserBaseRegistered, UserSensitiveInformation):
    """User registration class.

    Args:
        UserBase (_type_): BaseModel checker.
    """
    institution: institution_schema.InstitutionBase
    role: Optional[role_schema.RolesBase] = None


class UserProfile(UserBaseRegistered):
    """User Profile class.

        Args:
            UserBaseRegistered (_type_): BaseModel checker.
    """
    created_at: datetime
    updated_at: datetime
    active: bool
    status: str


class UserInput(UserBaseRegistered, UserSensitiveInformation):
    name: str
    last_name: str
    birthdate: date = Field(..., default_factory=date.today)
    country_id: Optional[int] = None
    document_number: str
    gender_id: Optional[int] = None
    institution: str
    role_id: Optional[int] = None
    contact_number: Optional[str] = None
