"""API endpoints for Account Takeover (ATO) risk evaluation."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.behaviour.service import UserBehaviourProfileService
from app.fraud.context import RuleContext
from app.fraud import create_default_engine
from app.security.account_takeover import AccountTakeoverDetector
from app.security.schemas import AccountTakeoverResponse

router = APIRouter(prefix="/users", tags=["Security & ATO"])


@router.get(
    "/{user_id}/account-takeover-risk",
    response_model=AccountTakeoverResponse,
    summary="Get Account Takeover Risk",
    description="Evaluate correlated threat signals indicating potential account takeover risk for a user.",
)
def get_user_account_takeover_risk(
    user_id: str,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' was not found",
        )

    # 1. Fetch user behaviour profile
    profile_service = UserBehaviourProfileService(db)
    profile = profile_service.get_user_profile(user_id)

    # 2. Fetch latest transaction if exists
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.timestamp.desc())
        .limit(1)
    )
    latest_txn = db.scalars(stmt).first()

    # 3. Construct RuleContext
    context = RuleContext(
        current_transaction=latest_txn or {"user_id": user_id},
        user=user,
        user_profile=profile,
    )

    # 4. Evaluate engine & correlate ATO signals
    engine = create_default_engine()
    results = engine.evaluate(context)
    detector = AccountTakeoverDetector()
    assessment = detector.evaluate(context, results)

    return assessment
