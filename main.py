from __future__ import annotations

import sys

from services.wallet_service import balance as wallet_balance
from helpers.menu import print_menu
from helpers.actions import (
    init_db_and_wallet,
    action_list_upcoming_games,
    action_view_previous_by_week,
    action_show_top25,
    action_create_slip,
    action_view_current_slips,
    action_view_settled_slips,
    action_view_all_slips,
    action_cancel_pending_slip,
)

def main():
    init_db_and_wallet()
    while True:
        try:
            print_menu(wallet_balance)
            choice = input("Select: ").strip()
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
        elif choice == "6":
            action_view_settled_slips()
        elif choice == "7":
            action_view_all_slips()
        elif choice == "8":
            action_cancel_pending_slip()
        else:
            print("Invalid choice.\n")

if __name__ == "__main__":
    main()
