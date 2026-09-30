"""API router exposing User Behaviour Profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.behaviour.service import UserBehaviourProfileService
from app.behaviour.schemas import UserBehaviourProfileResponse

router = APIRouter(prefix="/users", tags=["User Behaviour Profile"])


@router.get(
    "/{user_id}/behaviour-profile",
    response_model=UserBehaviourProfileResponse,
    summary="Get User Behaviour Profile",
    description="Retrieve the deterministic behavioural baseline calculated from a user's historical activity.",
)
def get_user_behaviour_profile(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve historical behavioural baseline for a given user."""
    service = UserBehaviourProfileService(db)
    profile = service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' was not found",
        )
    return profile
