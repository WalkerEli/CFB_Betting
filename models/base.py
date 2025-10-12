from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "storage.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
