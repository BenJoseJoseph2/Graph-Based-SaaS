from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import users, referral, rewards, fraud, dashboard

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cycle-Safe Referral Engine",
    description=(
        "A DAG-based referral system with real-time cycle detection, "
        "reward propagation, fraud detection, and a monitoring dashboard."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(referral.router)
app.include_router(rewards.router)
app.include_router(fraud.router)
app.include_router(dashboard.router)


@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "service": "Referral Engine"}
