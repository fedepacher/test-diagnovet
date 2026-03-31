from typing import Optional, Literal, List
from pydantic import BaseModel, Field

from api.app.schema import pagination_info_schema, profile_schema
from api.app.utils.global_def import ResultEnum, StatusEnum


class PatientId(BaseModel):
    """Represents the ID of a patient."""
    id: int

    class Config:
        from_attributes = True


class PatientInfo(BaseModel):
    name: str
    age: Optional[str] = None
    specie: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    is_neutered: Optional[bool] = None


class PatientBasicData(PatientId):
    """Basic patient information for list views."""
    name: str = Field(...)
    specie: Optional[str] = Field(None)
    breed: Optional[str] = Field(None)
    age: Optional[str] = Field(None)
    gender: Optional[str] = Field(None)
    is_neutered: Optional[bool] = Field(None)
    institution: str = Field(...)
    active: bool = Field(...)
    status: StatusEnum = Field(...)


class PatientInput(BaseModel):
    name: str = Field(..., description="Patient name")
    specie: Optional[int] = Field(None, description="Specie ID")
    breed: Optional[int] = Field(None, description="Specie ID")
    age: Optional[str] = Field(None, description="Age")
    gender_id: Optional[int] = Field(None, description="Gender ID")
    is_neutered: Optional[bool] = Field(None, description="If it is neutered")

    class Config:
        from_attributes = True


class PatientCreateForm(BaseModel):
    """Form for creating a new patient."""
    owner: profile_schema.Profile = Field(...)
    patient: PatientInput = Field(...)


class PaginatedPatientsResponse(BaseModel):
    """Paginated response for patient lists."""
    items: List[PatientBasicData]
    pagination: pagination_info_schema.PaginationInfo


class PatientResponse(PatientId):
    """Response model for patient operations."""
    status: Literal[ResultEnum.SUCCESS, ResultEnum.FAILURE]
