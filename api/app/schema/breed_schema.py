from pydantic import BaseModel, Field


class Breed(BaseModel):
    id: int
    name: str = Field(..., max_length=50, unique=True)

    class Config:
        from_attributes = True
