from typing import Iterable
from sqlalchemy import select, delete

from models.base import SessionLocal, Base, engine
from models.ranking import Ranking


def replace_rankings(new_ranks: Iterable[Ranking]):  # replace existing rankings with new ones
    with SessionLocal() as db:
        for r in new_ranks:
            db.execute(
                delete(Ranking).where(
                    (Ranking.season_year == r.season_year) &
                    (Ranking.week == r.week) &
                    (Ranking.poll == r.poll)
                )
            )
            db.add(r)
        db.commit()


def get_rankings(poll: str | None = None, season_year: int | None = None, week: int | None = None): # get rankings with optional filters
    with SessionLocal() as db:
        stmt = select(Ranking)
        if poll:
            stmt = stmt.where(Ranking.poll == poll)
        if season_year:
            stmt = stmt.where(Ranking.season_year == season_year)
        if week:
            stmt = stmt.where(Ranking.week == week)
        stmt = stmt.order_by(Ranking.rank.asc())
        return list(db.scalars(stmt))


def ensure_schema():
    Base.metadata.create_all(engine)
