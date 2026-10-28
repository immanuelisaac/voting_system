# app/models/__init__.py
# Re-export all models so that:
#   - `from app.models import User` works anywhere
#   - Alembic autogenerate sees every table through a single import

from .base import Base
from .user import User
from .election import Election, Candidate
from .vote import VoteCast, VoteTally

__all__ = ["Base", "User", "Election", "Candidate", "VoteCast", "VoteTally"]
