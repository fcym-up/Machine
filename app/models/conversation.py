"""Conversation message model — persistent multi-turn dialogue history."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime
from app.core.database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    session_id = Column(String(64), nullable=False, default="default", index=True)
    role = Column(String(16), nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
