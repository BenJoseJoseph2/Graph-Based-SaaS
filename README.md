# Cycle-Safe Referral Engine

A DAG-based referral system with real-time cycle detection, reward propagation, fraud detection, and a monitoring dashboard.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### 1. Database Setup
```sql
CREATE DATABASE referral_engine;
```

### 2. Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env: set DATABASE_URL to your PostgreSQL connection string

# Start the API server
uvicorn app.main:app --reload --port 8000

# In a separate terminal, seed the database
python seed.py
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### API Docs
After starting the backend, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables (backend/.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:password@localhost:5432/referral_engine` | PostgreSQL connection |
| `REWARD_DEPTH` | `3` | Levels to propagate rewards upward |
| `REWARD_PERCENT` | `10` | Base reward percentage |
| `VELOCITY_LIMIT` | `5` | Max referrals per referrer per window |
| `VELOCITY_WINDOW_SECONDS` | `60` | Velocity window in seconds |

## Key Features
- **Zero-cycle guarantee**: BFS-based cycle detection on every referral claim
- **3-layer fraud detection**: self-referral, duplicate, velocity limit
- **Reward propagation**: geometric decay across configurable depth levels
- **Real-time dashboard**: WebSocket + polling, graph visualization, fraud monitor
- **Simulation tool**: project reward costs before deploying new rules

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md) for full design details.
