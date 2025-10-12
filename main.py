from __future__ import annotations

import sys
import re
from typing import List, Tuple

import espn
from services.wallet_service import (
    ensure_schema as ensure_wallet_schema,
    reset_wallet,
    balance as wallet_balance,
    history as wallet_history,
)
from services.bet_service import (
    ensure_schema as ensure_bet_schema,
    create_slip,
    list_pending_slips,
)
from services.settlement_service import (
    ensure_schema as ensure_settle_schema,
)
try:
    from helpers.game_summary import print_summary
except Exception:  # pragma: no cover
    print_summary = None  # type: ignore

def init_db_and_wallet():
    # Ensure tables exist in the existing storage.db
    ensure_wallet_schema()
    ensure_bet_schema()
    ensure_settle_schema()

    # Deterministic wallet each run
    reset_wallet(1000.0)
    bal = wallet_balance()
    print(f"\nWallet balance reset to: {bal:.2f} tokens\n")


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


def _print_games(games, title: str):
    print(f"\n{title}")
    if not games:
        print("  (none)\n")
        return
    for g in games:
        # If the model has a label method, prefer it
        try:
            label = g.label()
        except Exception:
            score = (
                f"{g.away_score}-{g.home_score}"
                if (getattr(g, 'away_score', None) is not None and getattr(g, 'home_score', None) is not None)
                else "vs"
            )
            label = f"[{getattr(g, 'status', 'TBD')}] {g.away_team} @ {g.home_team} ({score})  {getattr(g, 'start', '')}"
        print(" ", label)
    print()


def _fetch_upcoming_games():
    sb = espn.get_scoreboard(week=None, seasontype=2)
    games = list(espn.parse_games(sb))
    return espn.filter_upcoming_games(games)


def _prompt_numeric_choice(prompt: str, lo: int, hi: int) -> int:
    while True:
        raw = input(prompt).strip()
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

        # Show a numbered list
        print(f"\nSelect game for Leg {leg_idx}:")
        numbered = []
        for i, g in enumerate(upcoming, start=1):
            # Skip already-chosen games to avoid duplicate legs (optional; can allow if you prefer)
            if getattr(g, "event_id", None) in used_event_ids:
                continue
            try:
                label = g.label()
            except Exception:
                label = f"{g.away_team} @ {g.home_team}  [{getattr(g,'status','TBD')}]  {getattr(g,'start','')}"
            print(f"  {i}) {label}")
            numbered.append((i, g))

        if not numbered:
            print("No selectable games remaining.\n")
            return []

        valid_numbers = [i for (i, _g) in numbered]
        idx = _prompt_numeric_choice(f"Pick 1–{max(valid_numbers)}: ", min(valid_numbers), max(valid_numbers))
        # Map idx to game (could have gaps if we skipped duplicates; search tuple list)
        selected = next((g for (i, g) in numbered if i == idx), None)
        if selected is None:
            print("Invalid selection; try again.")
            return _choose_legs_from_upcoming(num_legs - (leg_idx - 1))  # restart remaining

        # Winner choice
        print(f"\nWho wins?\n  1) {selected.home_team}\n  2) {selected.away_team}")
        win_choice = _prompt_numeric_choice("Select 1 or 2: ", 1, 2)
        pick_team = selected.home_team if win_choice == 1 else selected.away_team

        legs.append((str(selected.event_id), pick_team))
        used_event_ids.add(str(selected.event_id))

    return legs


def action_list_upcoming_games():
    upcoming = _fetch_upcoming_games()
    _print_games(upcoming, "Upcoming Games (current week)")


def action_view_previous_by_week():
    raw = input("Enter ESPN week number (1...20 regular season): ").strip()
    if not raw.isdigit():
        print("Invalid week.\n")
        return
    week = int(raw)
    sb = espn.get_scoreboard(week=week, seasontype=2)
    games = list(espn.parse_games(sb))
    finished = espn.filter_previous_games(games)
    _print_games(finished, f"Previous / Final Games — Week {week}")


def action_show_top25():
    rjson = espn.get_rankings()
    rankings = list(espn.parse_rankings(rjson))
    # Pretty print AP first
    ap = [r for r in rankings if (r.poll or "").lower().startswith("ap top 25")]
    rows = ap if ap else rankings
    if not rows:
        print("\nTop 25 Rankings\n  (none)\n")
        return

    def key_poll(r): return (0 if (r.poll or "").lower().startswith("ap top 25") else 1, r.rank)
    rows = sorted(rows, key=key_poll)
    print("\nTop 25 Rankings")
    current_poll = None
    shown_count = 0
    for r in rows:
        if current_poll != r.poll:
            current_poll = r.poll
            print(f"\n  {r.poll} — Week {r.week} ({r.season_year})")
            shown_count = 0
        if shown_count < 25:
            delta = ""
            if r.previous is not None and r.previous != 0:
                move = r.previous - r.rank
                if move > 0:
                    delta = f" (↑{move})"
                elif move < 0:
                    delta = f" (↓{-move})"
            print(f"   {r.rank:>2}. {r.team_name}{delta}")
            shown_count += 1
    print()

def action_create_slip():
    # Show wallet in the UI (display only)
    bal = wallet_balance()
    print(f"\nWallet (display only): {bal:.2f} tokens")

    # Ask legs
    print("\nCreate Slip — allowed legs: 1, 3, 5, 7")
    while True:
        raw = input("How many legs? ").strip()
        if not raw.isdigit():
            print("Enter a whole number (1, 3, 5, 7)")
            continue
        n = int(raw)
        if n not in {1, 3, 5, 7}:
            print("Leg count must be one of [1, 3, 5, 7].")
            continue
        break

    # Choose legs from numbered upcoming games (no typing of IDs)
    legs = _choose_legs_from_upcoming(n)
    if len(legs) != n:
        print("Could not build all legs (perhaps no upcoming games). Try again later.\n")
        return

    # Stake (display only)
    raw = input("\nEnter stake (tokens, display only): ")
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


def action_view_current_slips():
    slips = list_pending_slips()
    try:
        print("\nPending slips:\n")
        for s in slips:
            print(f"  Slip #{s.id}  legs={s.legs_count}  stake={s.stake_tokens:.2f}  status={s.status.value}\n")
    except Exception as e:
        print(f"(Could not print slips: {e})\n")
        return


# --------------------------------------------------------------------------------------
# Menu
# --------------------------------------------------------------------------------------

MENU = """--------------------------------------------------------------------------------
College Football CLI
--------------------------------------------------------------------------------
1) List upcoming games (current week, live)
2) View previous games by week (live)
3) Show Top 25 (live)
4) Create a bet slip (no wallet debit; status=PENDING)
5) View current slips (pending)
0) Exit
--------------------------------------------------------------------------------
Select: """


def main():
    init_db_and_wallet()

    while True:
        try:
            choice = input(MENU).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if choice == "0":
            print("Goodbye!")
            sys.exit(0)
        elif choice == "1":
            action_list_upcoming_games()
        elif choice == "2":
            action_view_previous_by_week()
        elif choice == "3":
            action_show_top25()
        elif choice == "4":
            action_create_slip()
        elif choice == "5":
            action_view_current_slips()
        else:
            print("Invalid choice.\n")


if __name__ == "__main__":
    main()
