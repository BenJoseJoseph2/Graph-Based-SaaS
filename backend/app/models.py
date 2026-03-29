from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class UserStatus(str, enum.Enum):
    active = "active"
    flagged = "flagged"
    suspended = "suspended"


class ReferralStatus(str, enum.Enum):
    valid = "valid"
    rejected = "rejected"
    pending = "pending"


class FraudReason(str, enum.Enum):
    cycle = "cycle"
    self_referral = "self_referral"
    velocity_limit = "velocity_limit"
    duplicate = "duplicate"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    referral_code = Column(String(20), unique=True, nullable=False)
    reward_balance = Column(Float, default=0.0)
    status = Column(SAEnum(UserStatus), default=UserStatus.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Referrals where this user is the referrer (parent)
    referrals_given = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    # Referral where this user is the new user (child)
    referral_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred", uselist=False)

    rewards_received = relationship("Reward", back_populates="user")
    fraud_flags = relationship("FraudFlag", back_populates="user")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(String, primary_key=True, default=generate_uuid)
    referred_id = Column(String, ForeignKey("users.id"), nullable=False)   # child (new user)
    referrer_id = Column(String, ForeignKey("users.id"), nullable=False)   # parent (who referred)
    status = Column(SAEnum(ReferralStatus), default=ReferralStatus.valid)
    is_primary = Column(Boolean, default=True)
    depth_level = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_given")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referral_received")


class Reward(Base):
    __tablename__ = "rewards"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    referral_id = Column(String, ForeignKey("referrals.id"), nullable=False)
    amount = Column(Float, nullable=False)
    depth_level = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="rewards_received")
    referral = relationship("Referral")


class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    attempted_referrer_id = Column(String, nullable=True)
    reason = Column(SAEnum(FraudReason), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="fraud_flags")


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String(50), nullable=False)   # referral_created, cycle_prevented, reward_distributed
    description = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
