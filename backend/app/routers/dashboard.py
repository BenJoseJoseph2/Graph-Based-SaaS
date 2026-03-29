from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import User, Referral, FraudFlag, Reward, ActivityEvent, ReferralStatus
from app.schemas import DashboardMetrics, ActivityEventOut, SimulationRequest, SimulationResult
from app.services.websocket_manager import manager
from app.services.reward_engine import simulate_rewards

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_referrals = db.query(func.count(Referral.id)).scalar() or 0
    valid_referrals = db.query(func.count(Referral.id)).filter(
        Referral.status == ReferralStatus.valid
    ).scalar() or 0
    rejected_referrals = db.query(func.count(Referral.id)).filter(
        Referral.status == ReferralStatus.rejected
    ).scalar() or 0
    fraud_attempts = db.query(func.count(FraudFlag.id)).scalar() or 0
    total_rewards = db.query(func.sum(Reward.amount)).scalar() or 0.0

    return DashboardMetrics(
        total_users=total_users,
        total_referrals=total_referrals,
        valid_referrals=valid_referrals,
        rejected_referrals=rejected_referrals,
        fraud_attempts=fraud_attempts,
        total_rewards_distributed=round(float(total_rewards), 2),
    )


@router.get("/activity", response_model=List[ActivityEventOut])
def get_activity(limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(ActivityEvent).order_by(
        ActivityEvent.created_at.desc()
    ).limit(limit).all()
    return events


@router.post("/simulate", response_model=SimulationResult)
def run_simulation(payload: SimulationRequest):
    result = simulate_rewards(
        referral_count=payload.referral_count,
        reward_percent=payload.reward_percent,
        reward_depth=payload.reward_depth,
        base_amount=payload.base_reward_amount,
    )
    return SimulationResult(**result)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive — client can also send pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
