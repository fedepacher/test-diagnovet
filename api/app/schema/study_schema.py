from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from api.app.schema import pagination_info_schema, patient_schema, veterinarian_schema


class StudyBase(BaseModel):
    """Represents the ID of a patient."""
    id: int
    study_type: str

    class Config:
        from_attributes = True


class PaginatedStudiesResponse(BaseModel):
    """Paginated response for patient lists."""
    items: List[StudyBase]
    pagination: pagination_info_schema.PaginationInfo


class StudyResultItem(BaseModel):
    key: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None


class StudyImageItem(BaseModel):
    id: int
    url: str
    description: Optional[str] = None


class StudyDetailSchema(BaseModel):
    id: int
    study_type: str
    study_date: Optional[datetime] = None

    observations: Optional[str] = None
    diagnosis: Optional[str] = None
    recommendations: Optional[str] = None

    created_at: datetime

    patient: patient_schema.PatientInfo
    veterinarian: Optional[veterinarian_schema.VeterinarianInfo] = None

    results: List[StudyResultItem] = []
    images: List[StudyImageItem] = []

    class Config:
        from_attributes = True