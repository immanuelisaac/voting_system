"""
test_models.py
--------------
Offline tests for the ORM layer — no live DB or FastAPI needed.

Tests cover:
  1. All models import cleanly
  2. Table names and column names are correct
  3. Privacy invariants (VoteCast has no candidate_id; VoteTally has no user_id)
  4. UniqueConstraint exists on VoteCast
  5. Settings loads without a .env file (defaults only)
  6. DATABASE_URL is well-formed
  7. UUID defaults are non-empty strings
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import UniqueConstraint

from app.models import Base, User, Election, Candidate, VoteCast, VoteTally
from app.core.config import settings


# ---------------------------------------------------------------------------
# 1. Import smoke test
# ---------------------------------------------------------------------------
def test_models_import():
    """All six model symbols must be importable without error."""
    assert Base is not None
    assert User is not None
    assert Election is not None
    assert Candidate is not None
    assert VoteCast is not None
    assert VoteTally is not None


# ---------------------------------------------------------------------------
# 2. Table names
# ---------------------------------------------------------------------------
def test_table_names():
    assert User.__tablename__ == "users"
    assert Election.__tablename__ == "elections"
    assert Candidate.__tablename__ == "candidates"
    assert VoteCast.__tablename__ == "votes_cast"
    assert VoteTally.__tablename__ == "vote_tallies"


# ---------------------------------------------------------------------------
# 3. User model — required columns present
# ---------------------------------------------------------------------------
def test_user_columns():
    cols = {c.name for c in User.__table__.columns}
    required = {"id", "username", "email", "hashed_password", "is_active", "is_admin",
                "created_at", "updated_at"}
    assert required.issubset(cols), f"Missing columns: {required - cols}"


# ---------------------------------------------------------------------------
# 4. Privacy invariant — VoteCast must NOT have candidate_id
# ---------------------------------------------------------------------------
def test_votecast_has_no_candidate_id():
    """Core privacy guarantee: participation receipt has no vote-choice column."""
    cols = {c.name for c in VoteCast.__table__.columns}
    assert "candidate_id" not in cols, (
        "PRIVACY BREACH: VoteCast must never contain candidate_id"
    )


# ---------------------------------------------------------------------------
# 5. Privacy invariant — VoteTally must NOT have user_id
# ---------------------------------------------------------------------------
def test_votetally_has_no_user_id():
    """Core privacy guarantee: anonymous counter has no identity column."""
    cols = {c.name for c in VoteTally.__table__.columns}
    assert "user_id" not in cols, (
        "PRIVACY BREACH: VoteTally must never contain user_id"
    )


# ---------------------------------------------------------------------------
# 6. Duplicate-vote prevention — UniqueConstraint on (user_id, election_id)
# ---------------------------------------------------------------------------
def test_votecast_unique_constraint():
    """DB-level guard against duplicate votes must exist."""
    constraints = VoteCast.__table__.constraints
    unique_cols_sets = [
        {c.name for c in uc.columns}
        for uc in constraints
        if isinstance(uc, UniqueConstraint)
    ]
    assert {"user_id", "election_id"} in unique_cols_sets, (
        "UniqueConstraint(user_id, election_id) is missing from VoteCast"
    )


# ---------------------------------------------------------------------------
# 7. VoteTally — candidate_id is unique (one row per candidate)
# ---------------------------------------------------------------------------
def test_votetally_candidate_unique():
    candidate_col = VoteTally.__table__.columns["candidate_id"]
    assert candidate_col.unique, "VoteTally.candidate_id must be UNIQUE"


# ---------------------------------------------------------------------------
# 8. Election -> Candidate relationship
# ---------------------------------------------------------------------------
def test_election_candidate_relationship():
    assert hasattr(Election, "candidates"), "Election must have .candidates relationship"
    assert hasattr(Candidate, "election"), "Candidate must have .election back-ref"


# ---------------------------------------------------------------------------
# 9. Settings defaults load correctly
# ---------------------------------------------------------------------------
def test_settings_defaults():
    assert settings.APP_NAME == "Online Voting System"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
    assert settings.DB_PORT == 3306


# ---------------------------------------------------------------------------
# 10. DATABASE_URL is well-formed
# ---------------------------------------------------------------------------
def test_database_url_format():
    url = settings.DATABASE_URL
    assert url.startswith("mysql+aiomysql://"), f"Bad URL scheme: {url}"
    assert settings.DB_NAME in url, "DB name missing from URL"
    assert str(settings.DB_PORT) in url, "DB port missing from URL"


# ---------------------------------------------------------------------------
# 11. UUID defaults generate non-empty strings
# ---------------------------------------------------------------------------
def test_uuid_defaults():
    u = User(username="test", email="t@t.com", hashed_password="x")
    e = Election(title="Test Election")
    assert u.id and len(u.id) == 36
    assert e.id and len(e.id) == 36
    assert u.id != e.id, "UUIDs must be unique per instance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
