from datetime import datetime
from pydantic import BaseModel, Field


class RolesBase(BaseModel):
    id: int
    name: str = Field(...)

    class Config:
        from_attributes = True


class Roles(RolesBase):
    description: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
