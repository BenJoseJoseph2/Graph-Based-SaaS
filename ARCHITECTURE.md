# Architecture Note — Cycle-Safe Referral Engine

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                React Dashboard (Port 3000)           │
│  MetricsPanel | GraphView | FraudPanel | ActivityFeed│
└──────────┬──────────────────────────┬───────────────┘
           │ HTTP (polling / REST)    │ WebSocket
           ▼                          ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend  (Port 8000)            │
│                                                     │
│  /referral/claim  →  FraudChecks → CycleDetector   │
│                       ↓ (if valid)                  │
│                    RewardEngine (DAG traversal)      │
│                                                     │
│  /dashboard/metrics  /fraud/flags  /user/:id/graph  │
│  /dashboard/ws  (WebSocket broadcast)               │
└──────────────────────┬──────────────────────────────┘
                       │ SQLAlchemy ORM
                       ▼
┌─────────────────────────────────────────────────────┐
│               PostgreSQL Database                    │
│  users | referrals | rewards | fraud_flags          │
│  activity_events                                    │
└─────────────────────────────────────────────────────┘
```

## Core Design Decisions

### 1. DAG Representation
- **Storage**: Adjacency list in PostgreSQL (`referrals` table, `referrer_id → referred_id`)
- **Direction**: Edge goes `child → parent` (referred → referrer)
- **Constraint**: One primary referrer per user (enforced at application level + DB query)

### 2. Cycle Detection Algorithm
- **Algorithm**: BFS from the attempted referrer, searching for the new user
- **Why BFS over DFS**: Better average-case performance on shallow graphs; early termination on first path found
- **Complexity**: O(V + E) over valid referrals only
- **SLA**: Easily meets <100ms for graphs up to ~100K nodes (typical referral networks)
- **Location**: `backend/app/services/cycle_detector.py`

```
Cycle check: Adding edge (new_user → referrer)
  → BFS from referrer
  → If new_user reachable: CYCLE (reject)
  → Else: SAFE (accept)
```

### 3. Reward Propagation
- Walks ancestors via `child_to_parent` map (O(depth))
- Geometric decay: Level 1 → 10%, Level 2 → 5%, Level 3 → 2.5%
- Configurable via `.env`: `REWARD_DEPTH`, `REWARD_PERCENT`
- All rewards committed atomically with the referral edge

### 4. Fraud Detection (3 checks)
1. **Self-referral**: `new_user_id == referrer_id`
2. **Duplicate referral**: User already has a valid primary referrer
3. **Velocity limit**: Referrer has exceeded N referrals in a rolling time window

### 5. Real-Time Updates
- WebSocket endpoint at `/dashboard/ws`
- `ConnectionManager` broadcasts events to all connected clients
- Events: `referral_created`, `cycle_prevented`, `fraud_detected`, `reward_distributed`
- Frontend falls back to polling (every 6s) if WebSocket disconnects

## Data Model

```sql
users         (id, name, email, referral_code, reward_balance, status, created_at)
referrals     (id, referred_id→users, referrer_id→users, status, is_primary, depth_level, created_at)
rewards       (id, user_id→users, referral_id→referrals, amount, depth_level, created_at)
fraud_flags   (id, user_id→users, attempted_referrer_id, reason, details, created_at)
activity_events (id, event_type, description, metadata_json, created_at)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/referral/claim` | Claim referral (runs all checks) |
| GET | `/referral/user/{id}/graph` | Get DAG subgraph for user |
| GET | `/user/{id}/rewards` | Get reward history |
| GET | `/fraud/flags` | List fraud attempts |
| GET | `/dashboard/metrics` | Aggregate metrics |
| GET | `/dashboard/activity` | Recent events |
| POST | `/dashboard/simulate` | Simulate reward costs |
| WS | `/dashboard/ws` | Real-time event stream |
| POST | `/users/` | Create user |
| GET | `/users/{id}` | Get user |

## Bonus Features Implemented
- **Simulation Tool**: Input reward rules → projected cost breakdown by depth
- **Real-time WebSocket**: Live dashboard updates on every referral/fraud event
- **Temporal design**: `created_at` on all records; ready for expiry queries
- **Hybrid graph support**: `is_primary` flag supports non-reward secondary edges
