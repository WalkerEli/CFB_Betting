from sqlalchemy import select
from models.base import SessionLocal, Base, engine
from models.bet import BetSlip, BetLeg, SlipStatus, LegResult
import espn

CREDIT_ON_WIN = False

def _credit_if_enabled(amount: float, reason: str):
    if not CREDIT_ON_WIN:
        return
    from services.wallet_service import credit
    credit(amount, reason)

def ensure_schema():
    Base.metadata.create_all(engine)

def _winner_from_summary(summary_json: dict) -> tuple[str | None, bool]:
    comps = (summary_json.get("header") or {}).get("competitions") or []
    if not comps:
        return None, False
    comp = comps[0]
    status = ((comp.get("status") or {}).get("type") or {}).get("state")
    is_final = (status or "").lower() == "post"

    competitors = (comp.get("competitors") or [])
    winner = None
    for c in competitors:
        if c.get("winner"):
            team = (c.get("team") or {})
            winner = team.get("displayName") or team.get("shortDisplayName") or team.get("name")
            break
    return winner, is_final

def _payout_multiplier(legs: int) -> float:
    return {1: 1.9, 3: 5.0, 5: 12.0, 7: 25.0}.get(legs, 1.0)

def check_and_settle() -> tuple[int, int]:
    checked = 0
    settled = 0

    with SessionLocal() as db:
        slips = list(db.scalars(select(BetSlip).where(BetSlip.status == SlipStatus.PENDING)))
        for slip in slips:
            checked += 1
            all_final = True
            wins = losses = 0

            for leg in slip.legs:
                if leg.result in (LegResult.WIN, LegResult.LOSS):
                    if leg.result == LegResult.WIN:
                        wins += 1
                    else:
                        losses += 1
                    continue

                summary_json = espn.get_summary(leg.event_id)  # your espn.py helper
                winner, is_final = _winner_from_summary(summary_json)
                if not is_final:
                    all_final = False
                    continue

                if winner and (winner == leg.pick_team_name):
                    leg.result = LegResult.WIN
                    wins += 1
                else:
                    leg.result = LegResult.LOSS
                    losses += 1
                db.add(leg)

            if all_final:
                needed = (slip.legs_count // 2) + 1
                if wins >= needed:
                    slip.status = SlipStatus.WON
                    # Optionally credit if desired:
                    if CREDIT_ON_WIN:
                        payout = round(slip.stake_tokens * _payout_multiplier(slip.legs_count), 2)
                        _credit_if_enabled(payout, f"Payout for {slip.legs_count}-leg slip #{slip.id}")
                else:
                    slip.status = SlipStatus.LOST
                slip.status = SlipStatus.SETTLED
                settled += 1

            db.add(slip)

        db.commit()

    return checked, settled
