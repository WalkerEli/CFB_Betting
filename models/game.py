from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String(32))
    start: Mapped[str | None] = mapped_column(String(40))  # ISO string

    home_team: Mapped[str] = mapped_column(String(80))
    away_team: Mapped[str] = mapped_column(String(80))
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def label(self) -> str:
        score = f"{self.away_score or 0}-{self.home_score or 0}" if (self.away_score is not None and self.home_score is not None) else "vs"
        return f"[{self.status or 'scheduled'}] {self.away_team} @ {self.home_team} ({score})  {self.start}"
