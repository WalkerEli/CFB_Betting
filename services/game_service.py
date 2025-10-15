from typing import Iterable
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models.base import SessionLocal, Base, engine
from models.game import Game


def save_games(games: Iterable[Game]) -> int:   # returns number of new games
    saved = 0
    with SessionLocal() as db:
        for g in games:
            try:
                db.add(g)
                db.commit()
                saved += 1
            except IntegrityError:
                db.rollback()  
    return saved


def list_games(limit: int = 25):    # list upcoming games (default 25)
    with SessionLocal() as db:
        stmt = select(Game).order_by(Game.start).limit(limit)
        return list(db.scalars(stmt))


def ensure_schema():    # create tables if not exist
    Base.metadata.create_all(engine)
