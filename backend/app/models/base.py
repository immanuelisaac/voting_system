# app/models/base.py
# Declarative base shared by all models.
# Keeping it in its own module breaks circular imports.

import uuid as _uuid

from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Central declarative base for all SQLAlchemy ORM models.

    UUID eagerness strategy:
      SQLAlchemy column `default=callable` fires only at INSERT time, so
      `instance.id` is None right after `Model()` — before any session flush.

      The `init` mapper event fires BEFORE _initialize_instance processes
      kwargs into attributes. By injecting `id` into the `kwargs` dict inside
      this event, SQLAlchemy's own attribute-setting pipeline picks it up and
      populates `instance.id` at construction time — no unsafe __setattr__ needed.
    """


@event.listens_for(Base, "init", propagate=True)
def _assign_uuid_on_init(target: Base, args: tuple, kwargs: dict) -> None:
    """
    Fired by SQLAlchemy BEFORE kwargs are mapped onto the new instance.
    Inject a UUID into kwargs so the ORM sets `id` during normal init.
    """
    table = getattr(target.__class__, "__table__", None)
    if table is not None and "id" in table.columns and "id" not in kwargs:
        kwargs["id"] = str(_uuid.uuid4())
