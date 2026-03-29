from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Reward, User
from app.schemas import UserRewardsResponse, RewardOut

router = APIRouter(prefix="/user", tags=["rewards"])


@router.get("/{user_id}/rewards", response_model=UserRewardsResponse)
def get_user_rewards(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rewards = db.query(Reward).filter(Reward.user_id == user_id).order_by(
        Reward.created_at.desc()
    ).all()

    total = sum(r.amount for r in rewards)

    return UserRewardsResponse(
        user_id=user_id,
        total_rewards=round(total, 2),
        rewards=[RewardOut.model_validate(r) for r in rewards],
    )
