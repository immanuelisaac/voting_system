# app/models/vote.py
# The privacy firewall between who voted and what they voted for.
#
#  VoteCast  — knows WHO voted and IN WHICH election  (no candidate link)
#  VoteTally — knows HOW MANY votes each candidate received  (no user link)
#
# Even a full DB dump cannot reconstruct individual ballots.

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VoteCast(Base):
    """
    Participation receipt — answers "Did user X vote in election Y?" ONLY.

    Design decisions:
      - Composite unique constraint on (user_id, election_id) is the
        database-level guarantee against duplicate votes.
      - There is deliberately NO candidate_id column here. Knowing that
        a user voted is enough to enforce integrity without breaking anonymity.
    """

    __tablename__ = "votes_cast"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "election_id",
            name="uq_user_election",
            comment="Each user may submit exactly one ballot per election",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ---------------------------------------------------------------------------
    # Who voted (identity reference)
    # ---------------------------------------------------------------------------
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------------------------
    # In which election (scope reference)
    # ---------------------------------------------------------------------------
    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------------------------
    # Audit
    # ---------------------------------------------------------------------------
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
        comment="Timestamp of ballot submission for audit trail",
    )

    # ---------------------------------------------------------------------------
    # Relationships (no candidate side — by design)
    # ---------------------------------------------------------------------------
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="vote_receipts",
    )
    election: Mapped["Election"] = relationship(  # noqa: F821
        "Election",
        back_populates="vote_casts",
    )

    def __repr__(self) -> str:
        return (
            f"<VoteCast user={self.user_id!r} election={self.election_id!r} "
            f"at={self.voted_at}>"
        )


class VoteTally(Base):
    """
    Anonymous aggregate counter — answers "How many votes did candidate Z get?"

    Design decisions:
      - No user_id column — ever. This table is the anonymised vote store.
      - vote_count is incremented atomically at the DB layer via
        UPDATE ... SET vote_count = vote_count + 1 to avoid race conditions.
      - One row per candidate, created when the election is set up.
    """

    __tablename__ = "vote_tallies"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ---------------------------------------------------------------------------
    # Which candidate this row counts for
    # ---------------------------------------------------------------------------
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,          # one tally row per candidate
        index=True,
    )

    # ---------------------------------------------------------------------------
    # The actual count — atomically incremented, never set directly
    # ---------------------------------------------------------------------------
    vote_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Use UPDATE vote_count = vote_count + 1 — never a raw SET",
    )

    # ---------------------------------------------------------------------------
    # Audit
    # ---------------------------------------------------------------------------
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    # ---------------------------------------------------------------------------
    # Relationships (no user side — by design)
    # ---------------------------------------------------------------------------
    candidate: Mapped["Candidate"] = relationship(  # noqa: F821
        "Candidate",
        back_populates="tally",
    )

    def __repr__(self) -> str:
        return (
            f"<VoteTally candidate={self.candidate_id!r} count={self.vote_count}>"
        )
