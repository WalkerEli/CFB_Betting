from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, DateTime
from datetime import datetime
from .base import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # single-user CLI: "default"
    balance: Mapped[float] = mapped_column(Float, default=0.0)

class WalletTx(Base):
    __tablename__ = "wallet_txs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[float] = mapped_column(Float)  # + credit / - debit
    reason: Mapped[str] = mapped_column(String(200), default="")
