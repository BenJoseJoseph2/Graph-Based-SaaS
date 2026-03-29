from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Reward, User
from app.schemas import UserRewardsResponse, RewardOut
from app.services.cycle_detector import get_descendants
from app.models import Referral, ReferralStatus

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


@router.get("/{user_id}/graph")
def get_user_graph(user_id: str, depth: int = 3, db: Session = Depends(get_db)):
    """GET /user/{id}/graph — required spec endpoint."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    descendants = get_descendants(db, user_id, max_depth=depth)
    all_user_ids = [user_id] + [d["user_id"] for d in descendants]
    users_map = {u.id: u for u in db.query(User).filter(User.id.in_(all_user_ids)).all()}

    nodes = []
    for d in [{"user_id": user_id, "depth": 0}] + descendants:
        u = users_map.get(d["user_id"])
        if u:
            nodes.append({
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "reward_balance": u.reward_balance,
                "status": u.status.value,
                "depth": d["depth"],
            })

    edges_raw = db.query(Referral).filter(
        Referral.referrer_id.in_(all_user_ids),
        Referral.referred_id.in_(all_user_ids),
        Referral.status == ReferralStatus.valid,
    ).all()

    edges = [{
        "source": e.referrer_id,
        "target": e.referred_id,
        "referral_id": e.id,
        "created_at": e.created_at.isoformat(),
    } for e in edges_raw]

    return {"nodes": nodes, "edges": edges, "root_user": user_id}
