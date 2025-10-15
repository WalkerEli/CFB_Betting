from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "storage.db") # ensure file is in storage dir
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)    # make dir if needed

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)  # initialize db engine

class Base(DeclarativeBase):    # base class for models
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) # session factory
