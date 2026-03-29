from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid, random, string

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


def _gen_referral_code(name: str) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    prefix = name[:3].upper().replace(" ", "")
    return f"{prefix}{suffix}"


@router.post("/", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    code = payload.referral_code or _gen_referral_code(payload.name)
    # Ensure uniqueness
    while db.query(User).filter(User.referral_code == code).first():
        code = _gen_referral_code(payload.name)

    user = User(
        id=str(uuid.uuid4()),
        name=payload.name,
        email=payload.email,
        referral_code=code,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# List route must be declared BEFORE /{user_id} to avoid FastAPI shadowing it
@router.get("/", response_model=list[UserOut])
def list_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
