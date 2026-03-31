from pydantic import BaseModel, Field


class Gender(BaseModel):
    id: int
    name: str = Field(..., max_length=15, unique=True)

    class Config:
        from_attributes = True
