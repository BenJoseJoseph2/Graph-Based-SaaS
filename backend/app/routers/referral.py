import uuid, json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Referral, ReferralStatus, User, FraudFlag, FraudReason, ActivityEvent, UserStatus
from app.schemas import ReferralClaimRequest, ReferralClaimResponse
from app.services.cycle_detector import would_create_cycle, get_descendants
from app.services.fraud_service import run_fraud_checks
from app.services.reward_engine import distribute_rewards
from app.services.websocket_manager import manager

router = APIRouter(prefix="/referral", tags=["referral"])


def _log_cycle_fraud(db: Session, new_user_id: str, referrer_id: str) -> FraudFlag:
    flag = FraudFlag(
        id=str(uuid.uuid4()),
        user_id=new_user_id,
        attempted_referrer_id=referrer_id,
        reason=FraudReason.cycle,
        details=f"Attempted referral would create a cycle: {new_user_id} -> {referrer_id}",
    )
    db.add(flag)
    db.add(ActivityEvent(
        id=str(uuid.uuid4()),
        event_type="cycle_prevented",
        description=f"Cycle prevented: {new_user_id} → {referrer_id}",
        metadata_json=json.dumps({
            "new_user_id": new_user_id,
            "referrer_id": referrer_id,
        }),
    ))
    user = db.query(User).filter(User.id == new_user_id).first()
    if user:
        user.status = UserStatus.flagged
    return flag


@router.post("/claim", response_model=ReferralClaimResponse)
async def claim_referral(payload: ReferralClaimRequest, db: Session = Depends(get_db)):
    # Resolve referrer by code
    referrer = db.query(User).filter(User.referral_code == payload.referrer_code).first()
    if not referrer:
        raise HTTPException(status_code=404, detail="Referrer code not found")

    new_user = db.query(User).filter(User.id == payload.new_user_id).first()
    if not new_user:
        raise HTTPException(status_code=404, detail="New user not found")

    referrer_id = referrer.id

    # ── Fraud checks (self, duplicate, velocity) ───────────────────────────
    is_fraud, reason_msg, fraud_flag = run_fraud_checks(db, payload.new_user_id, referrer_id)
    if is_fraud:
        # Store a rejected referral record so rejected_referrals metric is accurate
        db.add(Referral(
            id=str(uuid.uuid4()),
            referred_id=payload.new_user_id,
            referrer_id=referrer_id,
            status=ReferralStatus.rejected,
            is_primary=False,
        ))
        db.commit()
        await manager.broadcast("fraud_detected", {
            "user_id": payload.new_user_id,
            "reason": reason_msg,
        })
        return ReferralClaimResponse(
            success=False,
            message=reason_msg,
            fraud_flag_id=fraud_flag.id if fraud_flag else None,
        )

    # ── Cycle detection ────────────────────────────────────────────────────
    if would_create_cycle(db, payload.new_user_id, referrer_id):
        flag = _log_cycle_fraud(db, payload.new_user_id, referrer_id)
        # Store a rejected referral record so rejected_referrals metric is accurate
        db.add(Referral(
            id=str(uuid.uuid4()),
            referred_id=payload.new_user_id,
            referrer_id=referrer_id,
            status=ReferralStatus.rejected,
            is_primary=False,
        ))
        db.commit()
        await manager.broadcast("cycle_prevented", {
            "new_user_id": payload.new_user_id,
            "referrer_id": referrer_id,
        })
        return ReferralClaimResponse(
            success=False,
            message="Referral rejected: would create a cycle in the graph",
            fraud_flag_id=flag.id,
        )

    # ── Commit valid referral ──────────────────────────────────────────────
    referral = Referral(
        id=str(uuid.uuid4()),
        referred_id=payload.new_user_id,
        referrer_id=referrer_id,
        status=ReferralStatus.valid,
        is_primary=True,
        depth_level=1,
    )
    db.add(referral)

    db.add(ActivityEvent(
        id=str(uuid.uuid4()),
        event_type="referral_created",
        description=f"User {new_user.name} referred by {referrer.name}",
        metadata_json=json.dumps({
            "referred_id": payload.new_user_id,
            "referrer_id": referrer_id,
            "referral_id": referral.id,
        }),
    ))

    db.flush()  # ensure referral.id exists before reward distribution

    # ── Distribute rewards ─────────────────────────────────────────────────
    rewards = distribute_rewards(db, referral.id, payload.new_user_id)

    db.commit()

    await manager.broadcast("referral_created", {
        "referred_id": payload.new_user_id,
        "referrer_id": referrer_id,
        "rewards_count": len(rewards),
    })

    return ReferralClaimResponse(
        success=True,
        message="Referral accepted successfully",
        referral_id=referral.id,
        rewards_distributed=rewards,
    )


@router.get("/user/{user_id}/graph")
def get_user_graph(user_id: str, depth: int = 3, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    descendants = get_descendants(db, user_id, max_depth=depth)
    all_user_ids = [user_id] + [d["user_id"] for d in descendants]

    users_map = {
        u.id: u for u in db.query(User).filter(User.id.in_(all_user_ids)).all()
    }

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

    edges = [
        {
            "source": e.referrer_id,
            "target": e.referred_id,
            "referral_id": e.id,
            "created_at": e.created_at.isoformat(),
        }
        for e in edges_raw
    ]

    return {"nodes": nodes, "edges": edges, "root_user": user_id}
