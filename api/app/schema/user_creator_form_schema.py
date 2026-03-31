from pydantic import BaseModel, Field
from fastapi import Form
from typing import Optional


class UserCreateForm(BaseModel):
    email: str = Field(..., description="The user's email address.")
    username: str = Field(..., description="The user's chosen username.")
    password: str = Field(..., description="The user's password.")
    name: str = Field(..., description="The user's first name.")
    last_name: str = Field(..., description="The user's last name.")
    birthdate: str = Field(..., description="The user's birthdate in ISO format (YYYY-MM-DD).")
    country_id: int = Field(..., description="The user's country id.")
    document_number: str = Field(..., description="The user's document number.")
    gender_id: Optional[int] = Field(None, description="The user's gender id.")
    institution: str = Field(..., description="The user's institution.")
    role_id: Optional[int] = Field(None, description="The user's professional role id.")
    contact_number: Optional[str] = Field(None, description="The user's contact number.")

    @classmethod
    def as_form(
        cls,
        email: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
        name: str = Form(...),
        last_name: str = Form(...),
        birthdate: str = Form(...),
        country_id: int = Form(...),
        document_number: str = Form(...),
        gender_id: Optional[int] = Form(default=None),
        institution: str = Form(...),
        role_id: Optional[int] = Form(default=None),
        contact_number: Optional[str] = Form(default=None),
    ):
        return cls(
            email=email,
            username=username,
            password=password,
            name=name,
            last_name=last_name,
            birthdate=birthdate,
            country_id=country_id,
            document_number=document_number,
            gender_id=gender_id,
            institution=institution,
            role_id=role_id,
            contact_number=contact_number,
        )
