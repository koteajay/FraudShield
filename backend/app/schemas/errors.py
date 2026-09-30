"""Pydantic schemas for standardized API error responses."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(None, description="Optional extra error details or field errors")


class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(..., description="Error payload")
