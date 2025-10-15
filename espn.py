import requests
from typing import Iterable, List, Tuple
from models.game import Game
from models.ranking import Ranking

BASE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"

def get_scoreboard(week: int | None = None, seasontype: int = 2, dates: str | None = None) -> dict: # get scoreboard JSON from ESPN; seasontype=2 for regular season, 3 for postseason
    params = {"seasontype": seasontype}
    if week is not None:
        params["week"] = week
    if dates is not None:
        params["dates"] = dates
    r = requests.get(f"{BASE}/scoreboard", params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def get_summary(event_id: str) -> dict:  # get game summary JSON from ESPN for a given event ID
    r = requests.get(f"{BASE}/summary", params={"event": event_id}, timeout=20)
    r.raise_for_status()
    return r.json()

def get_rankings() -> dict:
    r = requests.get(f"{BASE}/rankings", timeout=20)
    r.raise_for_status()
    return r.json()

def parse_games(sb_json: dict) -> Iterable[Game]:   # parse games from ESPN scoreboard JSON
    season_year = (sb_json.get("season") or {}).get("year")
    week = ((sb_json.get("week") or {}) or {}).get("number")
    events = (sb_json.get("events") or []) or []
    for ev in events:
        event_id = ev.get("id")
        comp = (ev.get("competitions") or [{}])[0]
        status = ((comp.get("status") or {}).get("type") or {}).get("description", "scheduled")
        start = ev.get("date")
        competitors = (comp.get("competitors") or [])
        home, away = None, None
        for c in competitors:
            t = c.get("team") or {}
            # prefer displayName, fallback to location + name, shortDisplayName
            team_name = (
                t.get("displayName")
                or " ".join(x for x in [t.get("location"), t.get("name")] if x)
                or t.get("shortDisplayName")
                or "Unknown"
            )
            score = int(c.get("score")) if c.get("score") not in (None, "") else None
            if c.get("homeAway") == "home":
                home = (team_name, score)
            else:
                away = (team_name, score)
        if not (home and away):
            continue
        yield Game(
            event_id=str(event_id),
            week=week,
            season_year=season_year,
            status=status,
            start=start,
            home_team=home[0],
            away_team=away[0],
            home_score=home[1],
            away_score=away[1],
        )

def parse_rankings(r_json: dict) -> Iterable[Ranking]:  # parse rankings from ESPN rankings JSON
    season_year = (r_json.get("season") or {}).get("year")
    for poll_entry in (r_json.get("rankings") or []):
        poll_name = poll_entry.get("name") or "Unknown Poll"
        week = poll_entry.get("week", 0)
        for r in (poll_entry.get("ranks") or []):
            t = r.get("team") or {}
            team_name = (
                t.get("displayName")
                or " ".join(x for x in [t.get("location"), t.get("name")] if x)
                or t.get("shortDisplayName")
                or t.get("school")
                or t.get("nickname")
                or t.get("slug")
                or "Unknown"
            )
            yield Ranking(
                poll=poll_name,
                season_year=season_year or 0,
                week=week or 0,
                rank=r.get("current", 0),
                team_name=team_name,
                team_abbr=t.get("abbreviation") or t.get("shortName") or t.get("slug"),
                previous=r.get("previous"),
                points=r.get("points"),
                first_place_votes=r.get("firstPlaceVotes"),
            )

def _is_upcoming_status(s: str) -> bool:    # determine if a game status string indicates an upcoming (not started) game
    s = (s or "").lower()
    # ESPN strings seen for not-started games
    return ("sched" in s) or ("pre" in s) or ("upcoming" in s) or ("not started" in s)

def _is_final_status(s: str) -> bool:   # determine if a game status string indicates a final/finished game
    s = (s or "").lower()
    return ("final" in s) or ("post" in s) or ("end" in s)

def filter_upcoming_games(games: Iterable[Game]) -> List[Game]:  # filter games to only those that are upcoming (not started)
    return [g for g in games if _is_upcoming_status(g.status)]

def filter_previous_games(games: Iterable[Game]) -> List[Game]: # filter games to only those that are final/finished
    return [g for g in games if _is_final_status(g.status)]

def fetch_week_games(week: int | None, seasontype: int = 2) -> List[Game]:  # fetch and parse games for a given week and season type (2=regular, 3=postseason)
    sb = get_scoreboard(week=week, seasontype=seasontype)
    return list(parse_games(sb))

def extract_top25_from_rankings(r_json: dict) -> List[Tuple[int, str, str]]:  # extract top 25 rankings as (rank, team_name, poll_name) tuples from ESPN rankings JSON
    rankings = r_json.get("rankings") or []
    preferred_order = ["AP Top 25", "AFCA Coaches Poll"]
    chosen = None
    for name in preferred_order:
        for poll in rankings:
            if (poll.get("name") or "").strip() == name:
                chosen = poll
                break
        if chosen:
            break
    if not chosen and rankings:
        chosen = rankings[0]
    if not chosen:
        return []
    poll_name = chosen.get("name") or "Unknown Poll"
    out = []
    for r in (chosen.get("ranks") or [])[:25]:  # top 25 only
        t = r.get("team") or {}
        team_name = (
            t.get("displayName")
            or " ".join(x for x in [t.get("location"), t.get("name")] if x)
            or t.get("shortDisplayName")
            or t.get("school")
            or t.get("nickname")
            or t.get("slug")
            or "Unknown"
        )
        out.append((int(r.get("current", 0) or 0), team_name, poll_name))
    return out

def iter_full_season_weeks(year: int = 2025) -> List[Tuple[int, int]]:  # generate (seasontype, week) pairs for a full college football season
    pairs = []
    for w in range(1, 20 + 1):
        pairs.append((2, w))
    for w in range(1, 6):
        pairs.append((3, w))
    return pairs
