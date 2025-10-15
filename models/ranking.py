from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Ranking(Base):    # college football ranking entry
    __tablename__ = "rankings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    poll: Mapped[str] = mapped_column(String(40))         
    season_year: Mapped[int] = mapped_column(Integer)
    week: Mapped[int] = mapped_column(Integer)

    rank: Mapped[int] = mapped_column(Integer)
    team_name: Mapped[str] = mapped_column(String(100))
    team_abbr: Mapped[str | None] = mapped_column(String(20), nullable=True)
    previous: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_place_votes: Mapped[int | None] = mapped_column(Integer, nullable=True)
