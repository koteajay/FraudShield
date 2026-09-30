"""Transaction Journey REST API Router."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.journey.schemas import TransactionJourneyResponse
from app.journey.service import TransactionJourneyService

router = APIRouter(
    prefix="/transactions",
    tags=["Transaction Journey"],
)


@router.get(
    "/{transaction_id}/journey",
    response_model=TransactionJourneyResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Chronological Transaction Journey",
    description=(
        "Retrieves a normalized, chronological timeline of surrounding user activity "
        "(transactions, authentication attempts, device lifecycle events, triggered fraud rules, "
        "and risk flags) centered around the specified transaction."
    ),
)
def get_transaction_journey(
    transaction_id: str,
    before_minutes: Optional[int] = Query(
        default=30,
        description="Minutes before transaction to include in timeline",
    ),
    after_minutes: Optional[int] = Query(
        default=30,
        description="Minutes after transaction to include in timeline",
    ),
    db: Session = Depends(get_db),
) -> TransactionJourneyResponse:
    """Fetch chronological timeline surrounding transaction."""
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

    service = TransactionJourneyService()
    try:
        journey = service.get_transaction_journey(
            db=db,
            transaction_id=transaction_id,
            before_minutes=before_minutes,
            after_minutes=after_minutes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if journey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with identifier '{transaction_id}' was not found.",
        )

    return journey
