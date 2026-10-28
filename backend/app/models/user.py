# app/models/user.py
# Stores ONLY identity and credential data.
# This table has zero knowledge of what a user voted for.

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """
    Identity store — credentials and account state only.

    Privacy contract:
      - This table NEVER contains a candidate_id or any vote-choice column.
      - The only link to the vote subsystem is through VoteCast, which records
        *that* a user voted in an election but NOT *whom* they voted for.
    """

    __tablename__ = "users"

    # ---------------------------------------------------------------------------
    # Primary key: UUID string for non-guessable IDs
    # ---------------------------------------------------------------------------
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ---------------------------------------------------------------------------
    # Identity fields
    # ---------------------------------------------------------------------------
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique, case-sensitive login handle",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Used for account recovery; never exposed in vote queries",
    )

    # ---------------------------------------------------------------------------
    # Security fields
    # ---------------------------------------------------------------------------
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash — raw passwords are NEVER persisted",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Soft-disable accounts without data deletion",
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Admins can create/close elections",
    )

    # ---------------------------------------------------------------------------
    # Audit timestamps
    # ---------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    # One user -> many VoteCast receipts (one per election they participated in)
    vote_receipts: Mapped[list["VoteCast"]] = relationship(  # noqa: F821
        "VoteCast",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} username={self.username!r}>"
