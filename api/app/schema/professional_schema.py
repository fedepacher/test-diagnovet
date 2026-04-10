from pydantic import BaseModel
from typing import Optional


class ProfessionalInfo(BaseModel):
    name: str
    last_name: str
    license_number: Optional[str] = None
