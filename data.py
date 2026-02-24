from nba_api.stats.static import players, teams
import wikipedia
from cache import cache_manager
from datetime import datetime

# Set wikipedia language
wikipedia.set_lang("en")

def get_player_info(player_name):
    """Fetch player info from Static API + Wikipedia"""
    nba_players = players.get_players()
    found_player = next((p for p in nba_players if p['full_name'].lower() == player_name.lower()), None)
    
    if not found_player:
        return None

    cache_key = f"player_lite_{found_player['id']}"
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        return cached_data

    try:
        # Fetch summary from Wikipedia
        # We append "NBA" to ensure we get the basketball player
        summary = wikipedia.summary(f"{found_player['full_name']} NBA", sentences=4)
    except Exception:
        summary = "No biography available."

    result = {
        "id": found_player['id'],
        "full_name": found_player['full_name'],
        "is_active": found_player['is_active'],
        "summary": summary,
        "source": "Wikipedia (Lite Mode)",
        "stats": None  # Stats disabled to avoid blocking
    }
    
    cache_manager.set(cache_key, result)
    return result

def get_team_info(team_name):
    """Fetch team info from Static API + Wikipedia"""
    nba_teams = teams.get_teams()
    found_team = next((t for t in nba_teams if t['full_name'].lower() == team_name.lower() or t['nickname'].lower() == team_name.lower()), None)
    
    if not found_team:
        return None
    
    cache_key = f"team_lite_{found_team['id']}"
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Fetch general team history and info from Wikipedia
        summary = wikipedia.summary(f"{found_team['full_name']} NBA", sentences=4)
    except Exception:
        summary = "No team history available."

    result = {
        "id": found_team['id'],
        "full_name": found_team['full_name'],
        "summary": summary,
        "source": "Wikipedia (Lite Mode)",
        "stats": None
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