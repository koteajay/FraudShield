"""API endpoints for device registration, identification, and retrieval."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.devices.service import DeviceService
from app.devices.metadata import extract_device_metadata
from app.devices.schemas import (
    DeviceResponse,
    DeviceCreateRequest,
    DeviceCheckResponse,
)

router = APIRouter(prefix="/users", tags=["Devices"])


@router.get(
    "/{user_id}/devices",
    response_model=List[DeviceResponse],
    summary="List User Devices",
    description="Retrieve all client devices registered for a specified user.",
)
def list_user_devices(
    user_id: str,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' was not found",
        )
    service = DeviceService(db)
    return service.get_user_devices(user_id)


@router.post(
    "/{user_id}/devices",
    response_model=DeviceCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Register or Refresh Device",
    description="Identify, register, or refresh a client device from application telemetry and HTTP headers.",
)
def register_or_check_device(
    user_id: str,
    payload: DeviceCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' was not found",
        )

    # Fall back to request client IP and User-Agent if not explicitly in body
    ua = payload.user_agent or request.headers.get("user-agent")
    client_ip = payload.ip_address
    if not client_ip and request.client:
        client_ip = request.client.host

    service = DeviceService(db)
    metadata = extract_device_metadata(
        user_agent=ua,
        ip_address=client_ip,
        device_id=payload.device_id,
    )
    if payload.device_type:
        metadata = metadata.model_copy(update={"device_type": payload.device_type})

    device, is_new = service.get_or_create_device(user_id, metadata)
    return DeviceCheckResponse(
        user_id=user_id,
        device_id=device.device_id,
        is_known=not is_new,
        is_new_device=is_new,
        device=DeviceResponse.model_validate(device),
    )


@router.get(
    "/{user_id}/devices/{device_id}",
    response_model=DeviceResponse,
    summary="Get Device Details",
    description="Fetch a specific registered device for a user.",
)
def get_device_detail(
    user_id: str,
    device_id: str,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' was not found",
        )

    service = DeviceService(db)
    device = service.find_device(user_id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found for user '{user_id}'",
        )
    return device
