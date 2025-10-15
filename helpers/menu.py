from __future__ import annotations

# import standard modules
import os
from datetime import datetime
from typing import Any, Iterable

# get terminal width safely, with fallback
def term_width(default: int = 78) -> int:
    try:
        return max(60, min(120, os.get_terminal_size().columns))
    except Exception:
        return default

# create a horizontal line for ui
def line(ch: str = "-") -> str:
    return ch * term_width()

# print a formatted title bar
def title(text: str) -> None:
    width = term_width()
    print("\n" + "=" * width)
    centered = f" {text} ".center(width, " ")
    print(centered)
    print("=" * width)

# print section header with divider
def section(text: str) -> None:
    print("\n" + text)
    print(line("-"))

# print key-value formatted line
def kv(label: str, value: str) -> None:
    print(f"{label:<22}: {value}")

# simple input wrapper
def prompt(label: str) -> str:
    return input(label).strip()

# helper to format game info line
def _format_game_line(g: Any) -> str:
    status = f"{getattr(g, 'status', 'TBD')}".ljust(9)[:9]
    try:
        home = f"{g.home_team}"
        away = f"{g.away_team}"
    except Exception:
        home = getattr(g, "home_team", "HOME")
        away = getattr(g, "away_team", "AWAY")

    # default score text
    score = "vs"
    try:
        a = getattr(g, "away_score", None)
        h = getattr(g, "home_score", None)
        if a is not None and h is not None:
            score = f"{a}-{h}"
    except Exception:
        pass

    start = f"{getattr(g, 'start', '')}"
    return f"[{status}]  {away} @ {home}  ({score})  {start}"

# print a list of games with header
def print_games(games: Iterable[Any], header: str) -> None:
    section(header)
    empty = True
    for g in games:
        empty = False
        try:
            label = g.label()
        except Exception:
            label = _format_game_line(g)
        print("  " + label)
    if empty:
        print("  (none)")
    print()

# print a placeholder for empty data
def print_empty(parenthetical: str = "(none)") -> None:
    print(f"  {parenthetical}\n")

# print the main cli menu
def print_menu(wallet_balance_fn) -> None:
    # wallet_balance_fn is injected so we don't import services here
    title("College Football CLI")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    kv("Now", now)
    try:
        bal = wallet_balance_fn()
        kv("Wallet (display only)", f"{bal:.2f} tokens")
    except Exception:
        pass
    print(line("="))
    print("1) List upcoming games (live)")
    print("2) View previous games by week")
    print("3) Show Top 25 (live)")
    print("4) Create a bet slip (1, 3, 5, or 7 legs)")
    print("5) View current slips (pending)")
    print("6) View settled slips (pending/settled)")
    print("7) View all slips")
    print("8) Cancel a pending slip (if no legs underway)")
    print("0) Exit")
    print(line("="))
