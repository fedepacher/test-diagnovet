from pydantic import BaseModel
from typing import Optional


class VeterinarianInfo(BaseModel):
    name: str
    last_name: str
    license_number: Optional[str] = None
