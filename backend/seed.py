"""
Seed script — populates the database with test data including:
  - 10 users forming a valid DAG referral tree
  - 2 intentional fraud attempts (cycle + self-referral)
  - Rewards propagated automatically
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, Base, engine
from app.models import User, Referral, ReferralStatus, FraudFlag, FraudReason, ActivityEvent
from app.services.cycle_detector import would_create_cycle
from app.services.fraud_service import run_fraud_checks
from app.services.reward_engine import distribute_rewards
import uuid, json

Base.metadata.create_all(bind=engine)

db = SessionLocal()

def make_user(name: str, email: str, code: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing
    u = User(id=str(uuid.uuid4()), name=name, email=email, referral_code=code)
    db.add(u)
    db.flush()
    return u

def make_referral(new_user: User, referrer: User):
    """Create a valid referral edge with cycle detection."""
    is_fraud, msg, flag = run_fraud_checks(db, new_user.id, referrer.id)
    if is_fraud:
        print(f"  [FRAUD] {new_user.name} → {referrer.name}: {msg}")
        db.flush()
        return None

    if would_create_cycle(db, new_user.id, referrer.id):
        print(f"  [CYCLE] {new_user.name} → {referrer.name}: cycle detected!")
        flag = FraudFlag(
            id=str(uuid.uuid4()),
            user_id=new_user.id,
            attempted_referrer_id=referrer.id,
            reason=FraudReason.cycle,
            details="Seed: cycle detected",
        )
        db.add(flag)
        db.flush()
        return None

    ref = Referral(
        id=str(uuid.uuid4()),
        referred_id=new_user.id,
        referrer_id=referrer.id,
        status=ReferralStatus.valid,
        is_primary=True,
        depth_level=1,
    )
    db.add(ref)
    db.add(ActivityEvent(
        id=str(uuid.uuid4()),
        event_type="referral_created",
        description=f"{new_user.name} referred by {referrer.name}",
        metadata_json=json.dumps({"referred_id": new_user.id, "referrer_id": referrer.id}),
    ))
    db.flush()

    rewards = distribute_rewards(db, ref.id, new_user.id)
    print(f"  [OK]    {new_user.name} -> {referrer.name} | rewards: {rewards}")
    return ref


print("Creating users...")
alice   = make_user("Alice",   "alice@example.com",   "ALICE001")
bob     = make_user("Bob",     "bob@example.com",     "BOB0001")
carol   = make_user("Carol",   "carol@example.com",   "CAROL01")
dave    = make_user("Dave",    "dave@example.com",    "DAVE001")
eve     = make_user("Eve",     "eve@example.com",     "EVE0001")
frank   = make_user("Frank",   "frank@example.com",   "FRANK01")
grace   = make_user("Grace",   "grace@example.com",   "GRACE01")
henry   = make_user("Henry",   "henry@example.com",   "HENRY01")
irene   = make_user("Irene",   "irene@example.com",   "IRENE01")
jake    = make_user("Jake",    "jake@example.com",    "JAKE001")
db.commit()

print("\nBuilding referral tree (valid DAG):")
# Alice is root (no referrer)
# Tree:       Alice
#           /       \
#         Bob       Carol
#        / \          \
#     Dave  Eve      Frank
#      |              |
#    Grace           Henry
#      |
#    Irene
#      |
#    Jake

make_referral(bob,   alice)
make_referral(carol, alice)
make_referral(dave,  bob)
make_referral(eve,   bob)
make_referral(frank, carol)
make_referral(grace, dave)
make_referral(henry, frank)
make_referral(irene, grace)
make_referral(jake,  irene)
db.commit()

print("\nAttempting fraud scenarios:")
# Cycle attempt: Alice tries to use Jake's code (Jake is downstream of Alice)
print("  → Cycle attempt: Alice → Jake (should fail)")
if would_create_cycle(db, alice.id, jake.id):
    flag = FraudFlag(
        id=str(uuid.uuid4()),
        user_id=alice.id,
        attempted_referrer_id=jake.id,
        reason=FraudReason.cycle,
        details="Seed: Alice tried to refer under Jake (creates cycle Alice→Jake→...→Alice)",
    )
    db.add(flag)
    db.add(ActivityEvent(
        id=str(uuid.uuid4()),
        event_type="cycle_prevented",
        description="Cycle prevented: Alice → Jake",
        metadata_json=json.dumps({"new_user_id": alice.id, "referrer_id": jake.id}),
    ))
    print("  [CYCLE] Correctly prevented!")

# Self-referral
print("  → Self-referral: Bob refers Bob (should fail)")
is_fraud, msg, flag = run_fraud_checks(db, bob.id, bob.id)
if is_fraud:
    print(f"  [FRAUD] Correctly caught: {msg}")

db.commit()
print("\nSeed complete!")
print(f"  Users: {db.query(User).count()}")
print(f"  Valid referrals: {db.query(Referral).filter(Referral.status == ReferralStatus.valid).count()}")
print(f"  Fraud flags: {db.query(FraudFlag).count()}")
db.close()
