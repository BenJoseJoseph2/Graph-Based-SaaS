"""
Reward Engine — propagates rewards up the referral chain.

Config (from .env):
  REWARD_DEPTH   — how many levels up to reward (default: 3)
  REWARD_PERCENT — percentage of base amount (default: 10%)

Reward at each depth diminishes: depth 1 → 100%, depth 2 → 50%, depth 3 → 25%
(geometric decay) unless overridden.
"""

from typing import List, Dict
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Reward, User, ActivityEvent
from app.services.cycle_detector import get_ancestors
import uuid, json


BASE_REWARD_AMOUNT = 100.0  # Base unit; configurable per referral in future


def _reward_at_depth(base: float, percent: float, depth: int) -> float:
    """Geometric decay: each level up earns half of the level below."""
    rate = (percent / 100.0) / (2 ** (depth - 1))
    return round(base * rate, 2)


def distribute_rewards(
    db: Session,
    referral_id: str,
    new_user_id: str,
    base_amount: float = BASE_REWARD_AMOUNT,
) -> List[Dict]:
    """
    Walk up the referral chain and distribute rewards.
    Returns list of reward records created.
    """
    ancestors = get_ancestors(db, new_user_id, max_depth=settings.REWARD_DEPTH)
    distributed = []

    for ancestor_id, depth in ancestors:
        amount = _reward_at_depth(base_amount, settings.REWARD_PERCENT, depth)
        if amount <= 0:
            continue

        reward = Reward(
            id=str(uuid.uuid4()),
            user_id=ancestor_id,
            referral_id=referral_id,
            amount=amount,
            depth_level=depth,
        )
        db.add(reward)

        # Update user balance
        user = db.query(User).filter(User.id == ancestor_id).first()
        if user:
            user.reward_balance = round(user.reward_balance + amount, 2)

        # Log activity
        db.add(ActivityEvent(
            id=str(uuid.uuid4()),
            event_type="reward_distributed",
            description=f"Reward ₹{amount} distributed to user {ancestor_id} (depth {depth})",
            metadata_json=json.dumps({
                "user_id": ancestor_id,
                "amount": amount,
                "depth": depth,
                "referral_id": referral_id,
            }),
        ))

        distributed.append({
            "user_id": ancestor_id,
            "amount": amount,
            "depth": depth,
        })

    return distributed


def simulate_rewards(
    referral_count: int,
    reward_percent: float,
    reward_depth: int,
    base_amount: float = BASE_REWARD_AMOUNT,
) -> Dict:
    """
    Simulate projected reward cost without touching the database.
    """
    breakdown = []
    cost_per_referral = 0.0

    for depth in range(1, reward_depth + 1):
        amount = _reward_at_depth(base_amount, reward_percent, depth)
        # Assume each level has (depth) potential ancestors on average
        breakdown.append({
            "depth": depth,
            "reward_per_node": amount,
            "estimated_recipients_per_referral": 1,
            "subtotal_per_referral": amount,
        })
        cost_per_referral += amount

    total_cost = round(cost_per_referral * referral_count, 2)

    return {
        "total_referrals": referral_count,
        "reward_depth": reward_depth,
        "reward_percent": reward_percent,
        "projected_cost_per_referral": round(cost_per_referral, 2),
        "projected_total_cost": total_cost,
        "breakdown_by_depth": breakdown,
    }
