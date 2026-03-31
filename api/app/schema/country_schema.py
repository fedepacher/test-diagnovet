from pydantic import BaseModel, Field


class Country(BaseModel):
    id: int
    name: str = Field(..., max_length=50, unique=True)

    class Config:
        from_attributes = True
