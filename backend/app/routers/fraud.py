from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import FraudFlag
from app.schemas import FraudFlagOut

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.get("/flags", response_model=List[FraudFlagOut])
def get_fraud_flags(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    flags = db.query(FraudFlag).order_by(FraudFlag.created_at.desc()).offset(skip).limit(limit).all()
    return flags
