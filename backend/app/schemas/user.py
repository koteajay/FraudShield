"""Pydantic schemas for User entity."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import UserRole

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserBase(BaseModel):
    """Base schema for user identity fields."""
    email: str = Field(..., pattern=EMAIL_REGEX, description="Unique email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username handle")
    full_name: Optional[str] = Field(None, max_length=255, description="Full legal name")
    phone_number: Optional[str] = Field(None, max_length=50, description="Phone number")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Account active flag")
    is_verified: bool = Field(default=False, description="Account verification flag")


class UserCreate(UserBase):
    """Payload schema for user registration."""
    password: Optional[str] = Field(None, min_length=6, description="Plaintext password")
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Initial risk score")


class UserUpdate(BaseModel):
    """Payload schema for updating user attributes."""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)


class UserResponse(UserBase):
    """Response schema for User entity."""
    id: str
    risk_score: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
