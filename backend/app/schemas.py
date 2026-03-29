from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    active = "active"
    flagged = "flagged"
    suspended = "suspended"


class ReferralStatus(str, Enum):
    valid = "valid"
    rejected = "rejected"
    pending = "pending"


class FraudReason(str, Enum):
    cycle = "cycle"
    self_referral = "self_referral"
    velocity_limit = "velocity_limit"
    duplicate = "duplicate"


# ── User schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str
    referral_code: Optional[str] = None


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    referral_code: str
    reward_balance: float
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True


# ── Referral schemas ──────────────────────────────────────────────────────────

class ReferralClaimRequest(BaseModel):
    new_user_id: str
    referrer_code: str


class ReferralClaimResponse(BaseModel):
    success: bool
    message: str
    referral_id: Optional[str] = None
    fraud_flag_id: Optional[str] = None
    rewards_distributed: Optional[List[dict]] = None


class ReferralOut(BaseModel):
    id: str
    referred_id: str
    referrer_id: str
    status: ReferralStatus
    is_primary: bool
    depth_level: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Graph schemas ─────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    name: str
    email: str
    reward_balance: float
    status: UserStatus
    depth: int


class GraphEdge(BaseModel):
    source: str
    target: str
    referral_id: str
    created_at: datetime


class UserGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    root_user: str


# ── Reward schemas ────────────────────────────────────────────────────────────

class RewardOut(BaseModel):
    id: str
    user_id: str
    referral_id: str
    amount: float
    depth_level: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserRewardsResponse(BaseModel):
    user_id: str
    total_rewards: float
    rewards: List[RewardOut]


# ── Fraud schemas ─────────────────────────────────────────────────────────────

class FraudFlagOut(BaseModel):
    id: str
    user_id: str
    attempted_referrer_id: Optional[str]
    reason: FraudReason
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard schemas ─────────────────────────────────────────────────────────

class DashboardMetrics(BaseModel):
    total_users: int
    total_referrals: int
    valid_referrals: int
    rejected_referrals: int
    fraud_attempts: int
    total_rewards_distributed: float


# ── Activity schemas ──────────────────────────────────────────────────────────

class ActivityEventOut(BaseModel):
    id: str
    event_type: str
    description: str
    metadata_json: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Simulation schemas ────────────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    referral_count: int
    reward_percent: float
    reward_depth: int
    base_reward_amount: float = 100.0


class SimulationResult(BaseModel):
    total_referrals: int
    reward_depth: int
    reward_percent: float
    projected_cost_per_referral: float
    projected_total_cost: float
    breakdown_by_depth: List[dict]
