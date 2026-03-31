from pydantic import BaseModel, Field


class Specie(BaseModel):
    id: int
    name: str = Field(..., max_length=15, unique=True)

    class Config:
        from_attributes = True
