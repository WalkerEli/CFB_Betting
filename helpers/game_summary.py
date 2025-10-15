import espn


# simple helper to print a summary of an concluded event
def print_summary(event_id: str):
    data = espn.get_summary(event_id)
    header = (data.get("header") or {})
    comps = (header.get("competitions") or [])
    if not comps:
        print("No competition data.")
        return
    comp = comps[0]
    print("Status:", ((comp.get("status") or {}).get("type") or {}).get("description"))
    print("Date:", comp.get("date"))
    print("Venue:", ((comp.get("venue") or {}).get("fullName") or "Unknown"))
    print()
    for c in (comp.get("competitors") or []):
        team = (c.get("team") or {}).get("displayName")
        score = c.get("score")
        homeAway = c.get("homeAway")
        winner = "" if c.get("winner") else ""
        print(f"{homeAway:<5} {team:<32} {score:>4} {winner}")
