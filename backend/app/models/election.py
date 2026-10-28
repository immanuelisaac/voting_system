# app/models/election.py
# Election and Candidate metadata — describes what users are voting *on*.

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Election(Base):
    """
    Represents a single ballot / poll event.

    Lifecycle: draft -> active -> closed
    Only admins (User.is_admin=True) may create or close elections.
    """

    __tablename__ = "elections"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable election name shown on the ballot",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional longer description / voter guidance",
    )

    # ---------------------------------------------------------------------------
    # Lifecycle control
    # ---------------------------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Set True to open voting; False to close it",
    )
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Informational; enforcement can be done at API layer",
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ---------------------------------------------------------------------------
    # Audit
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
    candidates: Mapped[list["Candidate"]] = relationship(
        "Candidate",
        back_populates="election",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    vote_casts: Mapped[list["VoteCast"]] = relationship(  # noqa: F821
        "VoteCast",
        back_populates="election",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Election id={self.id!r} title={self.title!r} active={self.is_active}>"


class Candidate(Base):
    """
    A single option on the ballot for a given Election.
    """

    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Candidate / option display name",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional bio or policy blurb",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    election: Mapped["Election"] = relationship(
        "Election",
        back_populates="candidates",
    )
    # One-to-one tally record per candidate (created on first vote)
    tally: Mapped["VoteTally | None"] = relationship(  # noqa: F821
        "VoteTally",
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id!r} name={self.name!r}>"
