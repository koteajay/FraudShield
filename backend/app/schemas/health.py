"""Pydantic schemas for health and system metadata endpoints."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall service status")
    database: str = Field(default="connected", description="Database connectivity status")


class ApiInfoResponse(BaseModel):
    name: str = Field(..., description="Application name")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Runtime environment")
    status: str = Field(default="running", description="API running state")
