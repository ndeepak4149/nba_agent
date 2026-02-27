from nba_api.stats.static import players, teams
import wikipedia
from cache import cache_manager
from datetime import datetime
from config import DATA_MODE
from stats import get_player_season_stats, get_team_season_stats

wikipedia.set_lang("en")

_player_lookup = None
_team_lookup = None

def _initialize_lookups():
    """Builds fast, O(1) lookup dictionaries for players and teams on first use."""
    global _player_lookup, _team_lookup
    if _player_lookup is None:
        print("Initializing player lookup dictionary...")
        _player_lookup = {p['full_name'].lower(): p for p in players.get_players()}
    
    if _team_lookup is None:
        print("Initializing team lookup dictionary...")
        nba_teams = teams.get_teams()
        # Create a lookup for both full name and nickname
        _team_lookup = {t['full_name'].lower(): t for t in nba_teams}
        for t in nba_teams:
            if t['nickname']:
                _team_lookup[t['nickname'].lower()] = t

def get_player_info(player_name):
    """Fetch player info from Static API + Wikipedia"""
    _initialize_lookups()
    found_player = _player_lookup.get(player_name.lower())
    
    if not found_player:
        return None

    cache_key = f"player_lite_{found_player['id']}"
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        return cached_data

    try:
        # We append "NBA" to ensure we get the basketball player
        summary = wikipedia.summary(f"{found_player['full_name']} NBA", sentences=2)
    except Exception:
        summary = "No biography available."

    player_stats = None
    source = "Wikipedia (Lite Mode)"

    if DATA_MODE == "FULL":
        try:
            stats_data = get_player_season_stats(found_player['id'])
            if stats_data:
                player_stats = stats_data
                source = "nba_api (Full Mode)"
        except Exception as e:
            print(f"Could not fetch full stats for {player_name}: {e}")
            # Fallback to lite mode if full mode fails
            pass

    result = {
        "id": found_player['id'],
        "full_name": found_player['full_name'],
        "is_active": found_player['is_active'],
        "summary": summary,
        "source": source,
        "stats": player_stats
    }
    
    cache_manager.set(cache_key, result)
    return result

def get_team_info(team_name):
    """Fetch team info from Static API + Wikipedia"""
    _initialize_lookups()
    found_team = _team_lookup.get(team_name.lower())
    
    if not found_team:
        return None
    
    cache_key = f"team_lite_{found_team['id']}"
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        summary = wikipedia.summary(f"{found_team['full_name']} NBA", sentences=2)
    except Exception:
        summary = "No team history available."

    team_stats = None
    source = "Wikipedia (Lite Mode)"

    if DATA_MODE == "FULL":
        try:
            stats_data = get_team_season_stats(found_team['id'])
            if stats_data:
                team_stats = stats_data
                source = "nba_api (Full Mode)"
        except Exception as e:
            print(f"Could not fetch full stats for {team_name}: {e}")
            pass

    result = {
        "id": found_team['id'],
        "full_name": found_team['full_name'],
        "summary": summary,
        "source": source,
        "stats": team_stats
    }
    
    cache_manager.set(cache_key, result)
    return result

def get_all_players(limit=50):
    return [p['full_name'] for p in players.get_players()[:limit]]

def get_all_teams():
    return [t['full_name'] for t in teams.get_teams()]

def search_players_by_name(query, limit=10):
    return [p['full_name'] for p in players.get_players() if query.lower() in p['full_name'].lower()][:limit]

def get_live_games():
    """Stub for live games to avoid API blocks"""
    return [{
        "status": "Info",
        "matchup": "Live Data Disabled",
        "score": "N/A",
        "period": "Lite Mode"
    }]