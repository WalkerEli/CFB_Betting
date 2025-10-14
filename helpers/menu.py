from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Iterable

def term_width(default: int = 78) -> int:
    try:
        return max(60, min(120, os.get_terminal_size().columns))
    except Exception:
        return default

def line(ch: str = "-") -> str:
    return ch * term_width()

def title(text: str) -> None:
    width = term_width()
    print("\n" + "=" * width)
    centered = f" {text} ".center(width, " ")
    print(centered)
    print("=" * width)

def section(text: str) -> None:
    print("\n" + text)
    print(line("-"))

def kv(label: str, value: str) -> None:
    print(f"{label:<22}: {value}")

def prompt(label: str) -> str:
    return input(label).strip()

def _format_game_line(g: Any) -> str:
    status = f"{getattr(g, 'status', 'TBD')}".ljust(9)[:9]
    try:
        home = f"{g.home_team}"
        away = f"{g.away_team}"
    except Exception:
        home = getattr(g, "home_team", "HOME")
        away = getattr(g, "away_team", "AWAY")

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

def print_empty(parenthetical: str = "(none)") -> None:
    print(f"  {parenthetical}\n")

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
