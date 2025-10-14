from __future__ import annotations

from typing import List, Tuple
import re

import espn

from services.wallet_service import (
    ensure_schema as ensure_wallet_schema,
    reset_wallet,
    balance as wallet_balance,
)
from services.bet_service import (
    ensure_schema as ensure_bet_schema,
    create_slip,
    list_pending_slips,
    list_settled_slips,
    list_all_slips,
)
from services.settlement_service import (
    ensure_schema as ensure_settle_schema,
    cancel_pending_slip,
    check_and_settle,
)

from helpers.menu import (
    title,
    section,
    kv,
    prompt,
    print_games,
    print_empty,
)

try:
    from helpers.game_summary import print_summary  # noqa: F401
except Exception:  # pragma: no cover
    print_summary = None  # type: ignore




def init_db_and_wallet() -> None:
    ensure_wallet_schema()
    ensure_bet_schema()
    ensure_settle_schema()

    reset_wallet(1000.0)
    bal = wallet_balance()

    title("Initialized Database and Wallet")
    kv("Wallet balance reset to", f"{bal:.2f} tokens")
    try:
        _checked, settled = check_and_settle()
        if settled:
            print(f"[settlement] Updated {settled} slip(s).\n")
    except Exception as e:
        print(f"[settlement] Skipped: {e}\n")


# ------------------------------
# Internal helpers
# ------------------------------

def _parse_positive_float(raw: str) -> float | None:
    s = (raw or "").strip().replace(",", "").replace("$", "")
    m = re.match(r"^([-+]?[0-9]*\.?[0-9]+)", s)
    if not m:
        return None
    try:
        v = float(m.group(1))
        return v if v > 0 else None
    except Exception:
        return None

def _fetch_upcoming_games():
    try:
        sb = espn.get_scoreboard(week=None, seasontype=2)
    except Exception as e:
        print(f"\n[network] Could not load ESPN scoreboard: {e}\n")
        return []
    games = list(espn.parse_games(sb))
    return espn.filter_upcoming_games(games)

def _prompt_numeric_choice(label: str, lo: int, hi: int) -> int:
    while True:
        raw = prompt(label)
        if not raw.isdigit():
            print(f"Enter a number between {lo} and {hi}.")
            continue
        idx = int(raw)
        if idx < lo or idx > hi:
            print(f"Enter a number between {lo} and {hi}.")
            continue
        return idx

def _choose_legs_from_upcoming(num_legs: int) -> List[Tuple[str, str]]:
    legs: List[Tuple[str, str]] = []
    used_event_ids: set[str] = set()

    for leg_idx in range(1, num_legs + 1):
        upcoming = _fetch_upcoming_games()
        if not upcoming:
            print("\nNo upcoming games available right now.\n")
            return []

        section(f"Select game for Leg {leg_idx}")
        numbered = []
        for i, g in enumerate(upcoming, start=1):
            if getattr(g, "event_id", None) in used_event_ids:
                continue
            try:
                label = g.label()
            except Exception:
                # fall back to menu’s formatter via print_games (handled there),
                # but here we just show the label from g if available
                from helpers.menu import _format_game_line as _fmt  # local import to avoid exporting it
                label = _fmt(g)
            print(f"  {i:>2}) {label}")
            numbered.append((i, g))

        if not numbered:
            print("No selectable games remaining.\n")
            return []

        valid_numbers = [i for (i, _g) in numbered]
        idx = _prompt_numeric_choice(f"Pick 1–{max(valid_numbers)}: ", min(valid_numbers), max(valid_numbers))
        selected = next((g for (i, g) in numbered if i == idx), None)
        if selected is None:
            print("Invalid selection; try again.")
            return _choose_legs_from_upcoming(num_legs - (leg_idx - 1))  # restart remaining

        print("\nWho wins?")
        print(f"  1) {selected.home_team}")
        print(f"  2) {selected.away_team}")
        win_choice = _prompt_numeric_choice("Select 1 or 2: ", 1, 2)
        pick_team = selected.home_team if win_choice == 1 else selected.away_team

        legs.append((str(selected.event_id), pick_team))
        used_event_ids.add(str(selected.event_id))

    return legs


# ------------------------------
# Public actions
# ------------------------------

def action_list_upcoming_games() -> None:
    upcoming = _fetch_upcoming_games()
    print_games(upcoming, "Upcoming Games (current week)")

def action_view_previous_by_week() -> None:
    section("Previous Games By Week")
    raw = prompt("Enter ESPN week number (current regular season): ")
    if not raw.isdigit():
        print("Invalid week.\n")
        return
    week = int(raw)
    sb = espn.get_scoreboard(week=week, seasontype=2)
    games = list(espn.parse_games(sb))
    finished = espn.filter_previous_games(games)
    print_games(finished, f"Previous / Final Games — Week {week}")

def action_show_top25() -> None:
    rjson = espn.get_rankings()
    rankings = list(espn.parse_rankings(rjson))
    ap = [r for r in rankings if (r.poll or "").lower().startswith("ap top 25")]
    rows = ap if ap else rankings
    section("Top 25 Rankings")
    if not rows:
        print_empty()
        return

    def key_poll(r): 
        return (0 if (r.poll or "").lower().startswith("ap top 25") else 1, r.rank)

    rows = sorted(rows, key=key_poll)
    current_poll = None
    shown_count = 0
    for r in rows:
        if current_poll != r.poll:
            current_poll = r.poll
            print(f"\n  {r.poll} — Week {r.week} ({r.season_year})")
            print("  " + ("-" * 30))
            shown_count = 0
        if shown_count < 25:
            delta = ""
            if r.previous is not None and r.previous != 0:
                move = r.previous - r.rank
                if move > 0:
                    delta = f" (+{move})"
                elif move < 0:
                    delta = f" (-{-move})"
            print(f"   {r.rank:>2}. {r.team_name}{delta}")
            shown_count += 1
    print()

def action_create_slip() -> None:
    bal = wallet_balance()
    section("Create Slip")
    kv("Wallet (display only)", f"{bal:.2f} tokens")
    print("\nAllowed legs: 1, 3, 5, 7")

    while True:
        raw = prompt("How many legs? ")
        if not raw.isdigit():
            print("Enter a whole number (1, 3, 5, 7)")
            continue
        n = int(raw)
        if n not in {1, 3, 5, 7}:
            print("Leg count must be one of [1, 3, 5, 7].")
            continue
        break

    legs = _choose_legs_from_upcoming(n)
    if len(legs) != n:
        print("Could not build all legs (perhaps no upcoming games). Try again later.\n")
        return

    raw = prompt("\nEnter stake (tokens, display only): ")
    stake = _parse_positive_float(raw)
    if stake is None:
        print("Invalid stake; enter a positive number.\n")
        return

    slip, msg = create_slip(legs, stake)
    if slip is None:
        print("Failed to create slip:", msg, "\n")
        return

    print(
        f"\nCreated slip #{slip.id} with {slip.legs_count} legs, "
        f"stake {slip.stake_tokens:.2f}, status {slip.status.value}\n"
    )

def action_view_current_slips() -> None:
    try:
        check_and_settle()
    except Exception:
        pass

    slips = list_pending_slips()
    section("Current Slips (PENDING)")
    print()
    if not slips:
        print_empty()
        return
    for s in slips:
        print(f"  Slip #{s.id}  legs={s.legs_count}  stake={s.stake_tokens:.2f}  status={s.status.value}\n")

def action_view_settled_slips() -> None:
    try:
        check_and_settle()
    except Exception:
        pass

    slips = list_settled_slips()
    section("Settled Slips (WON/LOST/SETTLED)")
    print()
    if not slips:
        print_empty()
        return
    for s in slips:
        print(f"  Slip #{s.id}  legs={s.legs_count}  stake={s.stake_tokens:.2f}  status={s.status.value}\n")

def action_view_all_slips() -> None:
    try:
        check_and_settle()
    except Exception:
        pass

    slips = list_all_slips()
    section("All Slips (most recent first)")
    print()
    if not slips:
        print_empty()
        return
    for s in slips:
        print(f"  Slip #{s.id}  legs={s.legs_count}  stake={s.stake_tokens:.2f}  status={s.status.value}\n")

def action_cancel_pending_slip() -> None:
    try:
        check_and_settle()
    except Exception:
        pass

    slips = list_pending_slips()
    section("Cancel Pending Slip")
    print("Current slips (PENDING):\n")
    if not slips:
        print_empty()
        return
    for s in slips:
        print(f"  Slip #{s.id}  legs={s.legs_count}  stake={s.stake_tokens:.2f}  status={s.status.value}")
    print()

    raw = prompt("Enter the slip # to cancel (or press Enter to abort): ")
    if not raw:
        print("Canceled.\n")
        return
    if not raw.isdigit():
        print("Invalid slip #.\n")
        return

    ok, msg = cancel_pending_slip(int(raw))
    print("\n" + msg + "\n")
