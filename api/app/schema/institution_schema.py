from typing import Annotated, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from api.app.utils.global_def import ResultEnum


class InstitutionBase(BaseModel):
    """
    Base model for institution data.

    Defines the core structure for institution records in the database.
    """
    id: Annotated[int, Field(ge=0, description="Unique identifier for the institution")]
    """Institution ID, non-negative integer."""

    name: Annotated[str, Field(max_length=100, min_length=1, description="Institution name, up to 100 characters")]
    """Institution name."""

    class Config:
        """ doc """
        from_attributes = True


class Institution(InstitutionBase):
    """
    Extended model for institution data.

    Includes additional fields like category, subscription details, and audit fields based on the updated model.
    """
    active: Annotated[Optional[bool], Field(
        default=True,
        description="Whether the institution is active"
    )]
    """Active status of the institution."""

    status: Annotated[Optional[str], Field(
        max_length=20,
        default=None,
        description="Institution status, up to 20 characters, optional"
    )]
    """Current status of the institution."""

    created_at: Annotated[Optional[datetime], Field(
        default_factory=datetime.now,
        description="Timestamp when the institution was created"
    )]
    """Timestamp when the institution was created."""

    updated_at: Annotated[Optional[datetime], Field(
        default_factory=datetime.now,
        description="Timestamp when the institution was last updated"
    )]
    """Timestamp when the institution was last updated."""

    deleted_at: Annotated[Optional[datetime], Field(
        default=None,
        description="Timestamp when the institution was deleted, if applicable"
    )]
    """Timestamp when the institution was deleted, if applicable."""

    created_by: Annotated[Optional[int], Field(
        default=None,
        description="ID of the user who created the institution"
    )]
    """ID of the user who created the institution."""

    updated_by: Annotated[Optional[int], Field(
        default=None,
        description="ID of the user who last updated the institution"
    )]
    """ID of the user who last updated the institution."""

    deleted_by: Annotated[Optional[int], Field(
        default=None,
        description="ID of the user who deleted the institution"
    )]
    """ID of the user who deleted the institution."""

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        validate_assignment = True


class InstitutionResponse(BaseModel):
    """
    Base model for institution data.

    Defines the core structure for institution records in the database.
    """
    id: Annotated[int, Field(ge=0, description="Unique identifier for the institution")]
    """Institution ID, non-negative integer."""

    status: Annotated[ResultEnum, Field(
        default=ResultEnum.SUCCESS,
        description="Result status (e.g., SUCCESS, FAILURE)"
    )]
    """Result status (e.g., SUCCESS, FAILURE)."""

    class Config:
        """ doc """
        from_attributes = True
