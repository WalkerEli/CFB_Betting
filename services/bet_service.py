from typing import Sequence
from sqlalchemy import select
from models.base import SessionLocal, Base, engine
from models.bet import BetSlip, BetLeg, ALLOWED_LEGS

def ensure_schema():
    Base.metadata.create_all(engine)

def create_slip(legs_input: Sequence[tuple[str, str]], stake_tokens: float) -> tuple[BetSlip | None, str]:
    """
    Simplified:
    - NO wallet checks
    - NO debit
    - Just record a PENDING slip + legs
    """
    n = len(legs_input)
    if n not in ALLOWED_LEGS:
        return None, f"Leg count must be one of {sorted(ALLOWED_LEGS)}."

    try:
        stake = float(stake_tokens)
    except Exception:
        return None, "Stake must be a number."
    if stake <= 0:
        return None, "Stake must be > 0."

    slip = BetSlip(legs_count=n, stake_tokens=stake)  # status defaults to PENDING
    slip.legs = [BetLeg(event_id=eid, pick_team_name=team) for (eid, team) in legs_input]

    with SessionLocal() as db:
        db.add(slip)
        db.commit()
        db.refresh(slip)
        return slip, "OK"

def list_pending_slips():
    with SessionLocal() as db:
        stmt = select(BetSlip).where(BetSlip.status == "PENDING").order_by(BetSlip.created_at.asc())
        return list(db.scalars(stmt))
    
def list_settled_slips(limit: int = 50):
    with SessionLocal() as db:
        stmt = select(BetSlip).where(BetSlip.status == "SETTLED").order_by(BetSlip.created_at.desc()).limit(limit)
        return list(db.scalars(stmt))

def list_all_slips(limit: int = 50):
    with SessionLocal() as db:
        stmt = select(BetSlip).order_by(BetSlip.created_at.desc()).limit(limit)
        return list(db.scalars(stmt))
