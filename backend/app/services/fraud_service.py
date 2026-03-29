"""
Fraud detection service.

Checks (in order):
  1. Self-referral — new_user == referrer
  2. Duplicate referral — new_user already has a primary referrer
  3. Velocity limit — referrer has made too many referrals in the last window
  4. Cycle detection (delegated to cycle_detector)
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.models import Referral, FraudFlag, FraudReason, User, ReferralStatus, ActivityEvent, UserStatus
import uuid, json


def _log_fraud(
    db: Session,
    user_id: str,
    attempted_referrer_id: str,
    reason: FraudReason,
    details: str,
) -> FraudFlag:
    flag = FraudFlag(
        id=str(uuid.uuid4()),
        user_id=user_id,
        attempted_referrer_id=attempted_referrer_id,
        reason=reason,
        details=details,
    )
    db.add(flag)

    # Flag user if they keep triggering fraud
    existing_flags = db.query(func.count(FraudFlag.id)).filter(
        FraudFlag.user_id == user_id
    ).scalar()
    if existing_flags and existing_flags >= 3:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.status = UserStatus.flagged

    db.add(ActivityEvent(
        id=str(uuid.uuid4()),
        event_type="fraud_detected",
        description=f"Fraud [{reason.value}] detected for user {user_id}",
        metadata_json=json.dumps({
            "user_id": user_id,
            "attempted_referrer_id": attempted_referrer_id,
            "reason": reason.value,
            "details": details,
        }),
    ))

    return flag


def check_self_referral(new_user_id: str, referrer_id: str) -> bool:
    return new_user_id == referrer_id


def check_duplicate_referral(db: Session, new_user_id: str) -> bool:
    """Return True if new_user already has a valid primary referral."""
    existing = db.query(Referral).filter(
        Referral.referred_id == new_user_id,
        Referral.is_primary == True,
        Referral.status == ReferralStatus.valid,
    ).first()
    return existing is not None


def check_velocity_limit(db: Session, referrer_id: str) -> bool:
    """Return True if referrer has exceeded the velocity limit."""
    window_start = datetime.now(timezone.utc) - timedelta(
        seconds=settings.VELOCITY_WINDOW_SECONDS
    )
    count = db.query(func.count(Referral.id)).filter(
        Referral.referrer_id == referrer_id,
        Referral.created_at >= window_start,
        Referral.status == ReferralStatus.valid,
    ).scalar()
    return (count or 0) >= settings.VELOCITY_LIMIT


def run_fraud_checks(
    db: Session,
    new_user_id: str,
    referrer_id: str,
) -> tuple[bool, str | None, FraudFlag | None]:
    """
    Run all fraud checks (except cycle detection which is in cycle_detector).
    Returns (is_fraud, reason_message, fraud_flag_or_None).
    """
    # 1. Self-referral
    if check_self_referral(new_user_id, referrer_id):
        flag = _log_fraud(
            db, new_user_id, referrer_id,
            FraudReason.self_referral,
            "User attempted to refer themselves",
        )
        return True, "Self-referral is not allowed", flag

    # 2. Duplicate
    if check_duplicate_referral(db, new_user_id):
        flag = _log_fraud(
            db, new_user_id, referrer_id,
            FraudReason.duplicate,
            "User already has an active referral",
        )
        return True, "User already has an active referral", flag

    # 3. Velocity
    if check_velocity_limit(db, referrer_id):
        flag = _log_fraud(
            db, referrer_id, referrer_id,
            FraudReason.velocity_limit,
            f"Referrer exceeded {settings.VELOCITY_LIMIT} referrals in {settings.VELOCITY_WINDOW_SECONDS}s",
        )
        return True, "Referrer has exceeded the velocity limit", flag

    return False, None, None
