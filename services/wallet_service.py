from sqlalchemy import select
from models.base import SessionLocal, Base, engine
from models.wallet import Wallet, WalletTx
from datetime import datetime

DEFAULT_OWNER = "default"


def ensure_schema():
    Base.metadata.create_all(engine)


def _get_wallet(db, owner: str = DEFAULT_OWNER) -> Wallet:
    w = db.scalar(select(Wallet).where(Wallet.owner == owner))
    if not w:
        w = Wallet(owner=owner, balance=0.0)
        db.add(w)
        db.commit()
        db.refresh(w)
    return w


def reset_wallet(target_amount: float, owner: str = DEFAULT_OWNER) -> None:
    """
    Set wallet balance to 'target_amount' every time the app starts.
    Writes a single WalletTx for the delta (audit-friendly), but keeps it simple.
    """
    with SessionLocal() as db:
        w = _get_wallet(db, owner)
        target = float(target_amount)
        current = float(w.balance or 0.0)
        delta = round(target - current, 2)
        if abs(delta) < 1e-9:
            return  # already at target
        w.balance = target
        if delta != 0.0:
            db.add(WalletTx(
                created_at=datetime.utcnow(),
                owner=owner,
                amount=delta,
                reason=f"Wallet reset to {target:.2f}"
            ))
        db.add(w)
        db.commit()


def credit(amount: float, reason: str = "", owner: str = DEFAULT_OWNER) -> bool:
    try:
        amt = float(amount)
    except Exception:
        return False
    if amt <= 0:
        return False

    with SessionLocal() as db:
        w = _get_wallet(db, owner)
        w.balance = float(w.balance) + amt
        db.add(WalletTx(owner=owner, amount=amt, reason=reason or "credit"))
        db.add(w)
        db.commit()
        return True


def debit(amount: float, reason: str = "", owner: str = DEFAULT_OWNER) -> bool:
    """
    Kept for completeness but NOT used in simplified flow.
    """
    try:
        amt = float(amount)
    except Exception:
        return False
    if amt <= 0:
        return False

    with SessionLocal() as db:
        w = _get_wallet(db, owner)
        if float(w.balance) < amt:
            return False
        w.balance = float(w.balance) - amt
        db.add(WalletTx(owner=owner, amount=-amt, reason=reason or "debit"))
        db.add(w)
        db.commit()
        return True


def balance(owner: str = DEFAULT_OWNER) -> float:
    with SessionLocal() as db:
        w = db.scalar(select(Wallet).where(Wallet.owner == owner))
        return float(w.balance if w else 0.0)


def history(limit: int = 50, owner: str = DEFAULT_OWNER):
    with SessionLocal() as db:
        stmt = (
            select(WalletTx)
            .where(WalletTx.owner == owner)
            .order_by(WalletTx.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))
