"""Users REST API Router for Behavioural Profiles and User-level Journey Timelines."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.behaviour.schemas import UserBehaviourProfileResponse
from app.behaviour.service import UserBehaviourProfileService
from app.journey.schemas import TransactionJourneyResponse
from app.journey.service import TransactionJourneyService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/{id}/profile",
    response_model=UserBehaviourProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User Fraud Behaviour Profile",
    description=(
        "Retrieves the established behavioural baseline profile for a specific user, "
        "including normal spending amounts, transaction frequency, known locations, "
        "active hours of the day, recognized devices, and authentication failure statistics."
    ),
)
def get_user_profile(
    id: str,
    db: Session = Depends(get_db),
) -> UserBehaviourProfileResponse:
    """Retrieve user fraud behaviour profile."""
    # Verify user exists
    user = db.query(User).filter(User.id == id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with identifier '{id}' was not found.",
        )

    service = UserBehaviourProfileService(db)
    profile = service.get_user_profile(id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with identifier '{id}' was not found.",
        )
    return UserBehaviourProfileResponse(**profile.model_dump())


@router.get(
    "/{id}/journey",
    response_model=TransactionJourneyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User-Level Activity Journey Timeline",
    description=(
        "Retrieves a chronological journey timeline of all activities (transactions, "
        "authentication attempts, device events, and fraud rules) for a specific user "
        "within an investigation window."
    ),
)
def get_user_journey(
    id: str,
    before_minutes: Optional[int] = Query(
        default=60,
        description="Minutes before anchor/latest activity to include in timeline",
    ),
    after_minutes: Optional[int] = Query(
        default=0,
        description="Minutes after anchor/latest activity to include in timeline",
    ),
    db: Session = Depends(get_db),
) -> TransactionJourneyResponse:
    """Retrieve chronological activity journey for a user."""
    user = db.query(User).filter(User.id == id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with identifier '{id}' was not found.",
        )

    if before_minutes is not None and before_minutes < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter 'before_minutes' cannot be negative.",
        )
    if after_minutes is not None and after_minutes < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter 'after_minutes' cannot be negative.",
        )

    journey_service = TransactionJourneyService()
    try:
        journey = journey_service.get_user_journey(
            db=db,
            user_id=id,
            before_minutes=before_minutes,
            after_minutes=after_minutes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return journey
