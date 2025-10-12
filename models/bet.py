from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, Float
from datetime import datetime
from enum import Enum as PyEnum
from .base import Base

ALLOWED_LEGS = {1, 3, 5, 7}

class SlipStatus(PyEnum):
    PENDING = "PENDING"
    WON = "WON"
    LOST = "LOST"
    SETTLED = "SETTLED"

class LegResult(PyEnum):
    PENDING = "PENDING"
    WIN = "WIN"
    LOSS = "LOSS"
    PUSH = "PUSH"  # not used yet, but handy

class BetSlip(Base):
    __tablename__ = "bet_slips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    legs_count: Mapped[int] = mapped_column(Integer)
    stake_tokens: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[SlipStatus] = mapped_column(Enum(SlipStatus), default=SlipStatus.PENDING)

    legs: Mapped[list[BetLeg]] = relationship("BetLeg", back_populates="slip", cascade="all, delete-orphan")

    def required_wins(self) -> int:
        # strictly more than 50%
        return (self.legs_count // 2) + 1

    def wins_losses(self) -> tuple[int, int]:
        wins = sum(1 for l in self.legs if l.result == LegResult.WIN)
        losses = sum(1 for l in self.legs if l.result == LegResult.LOSS)
        return wins, losses

class BetLeg(Base):
    __tablename__ = "bet_legs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slip_id: Mapped[int] = mapped_column(ForeignKey("bet_slips.id", ondelete="CASCADE"))
    event_id: Mapped[str] = mapped_column(String(32), index=True)

    # store a human-stable reference for winner selection
    pick_team_name: Mapped[str] = mapped_column(String(100))  # user’s chosen winner
    result: Mapped[LegResult] = mapped_column(Enum(LegResult), default=LegResult.PENDING)

    slip: Mapped[BetSlip] = relationship("BetSlip", back_populates="legs")
