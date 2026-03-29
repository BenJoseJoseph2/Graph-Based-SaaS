"""
Cycle detection service using BFS on the in-memory adjacency list.

Graph direction: adj[referrer] -> [referred, ...] (parent -> children).
Adding a new referral stores edge: adj[referrer].append(new_user).

A cycle exists if new_user can ALREADY reach referrer via the current graph
before we add the new edge. i.e. new_user is already an ancestor of referrer.

Detection: has_path(adj, new_user_id, referrer_id)
  - If True  → new_user is upstream of referrer → adding referrer->new_user creates cycle → REJECT
  - If False → safe to add edge
"""

from collections import defaultdict, deque
from typing import Dict, List, Set
from sqlalchemy.orm import Session
from app.models import Referral, ReferralStatus


def _build_adjacency(db: Session) -> Dict[str, List[str]]:
    """Build parent→children adjacency list from valid referrals."""
    adj: Dict[str, List[str]] = defaultdict(list)
    rows = db.query(Referral.referrer_id, Referral.referred_id).filter(
        Referral.status == ReferralStatus.valid
    ).all()
    for referrer_id, referred_id in rows:
        # Edge direction: referrer → referred (parent → child)
        adj[referrer_id].append(referred_id)
    return adj


def has_path(adj: Dict[str, List[str]], start: str, target: str) -> bool:
    """BFS: does a path exist from `start` to `target` in the DAG?"""
    if start == target:
        return True
    visited: Set[str] = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in adj.get(node, []):
            if neighbor == target:
                return True
            if neighbor not in visited:
                queue.append(neighbor)
    return False


def would_create_cycle(db: Session, new_user_id: str, referrer_id: str) -> bool:
    """
    Check if adding referrer->new_user edge would create a cycle.
    A cycle exists if new_user can already reach referrer via current edges
    (i.e., new_user is already an ancestor of referrer).

    Runtime: O(V + E) — well within the 100ms SLA for typical graph sizes.
    """
    adj = _build_adjacency(db)
    # Cycle: can new_user already reach referrer through existing parent->child edges?
    return has_path(adj, new_user_id, referrer_id)


def get_ancestors(db: Session, user_id: str, max_depth: int = 10) -> List[tuple]:
    """
    Return (ancestor_id, depth) tuples walking up the referral chain.
    Used by the reward engine.
    """
    # Build child→parent map
    child_to_parent: Dict[str, str] = {}
    rows = db.query(Referral.referred_id, Referral.referrer_id).filter(
        Referral.status == ReferralStatus.valid,
        Referral.is_primary == True
    ).all()
    for referred_id, referrer_id in rows:
        child_to_parent[referred_id] = referrer_id

    ancestors = []
    current = user_id
    depth = 1
    visited: Set[str] = set()
    while depth <= max_depth:
        parent = child_to_parent.get(current)
        if not parent or parent in visited:
            break
        ancestors.append((parent, depth))
        visited.add(parent)
        current = parent
        depth += 1
    return ancestors


def get_descendants(db: Session, user_id: str, max_depth: int = 5) -> List[dict]:
    """
    Return descendant nodes with depth info for graph visualization.
    """
    adj = _build_adjacency(db)

    result = []
    visited: Set[str] = set()
    queue = deque([(user_id, 0)])

    while queue:
        node, depth = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        if node != user_id:
            result.append({"user_id": node, "depth": depth})
        if depth < max_depth:
            for child in adj.get(node, []):
                if child not in visited:
                    queue.append((child, depth + 1))

    return result
