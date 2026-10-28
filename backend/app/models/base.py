# app/models/base.py
# Declarative base shared by all models.
# Keeping it in its own module breaks circular imports.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Central declarative base for all SQLAlchemy ORM models."""
    pass
