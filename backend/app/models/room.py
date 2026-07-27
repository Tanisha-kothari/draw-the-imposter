import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    num_rounds: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    drawing_time: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    voting_time: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    num_imposters: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    word_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="waiting", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    players = relationship("Player", back_populates="room", cascade="all, delete-orphan")
    games = relationship("Game", back_populates="room", cascade="all, delete-orphan")
