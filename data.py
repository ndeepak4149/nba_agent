from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playercareerstats
import pandas as pd

def get_player_info(player_name):
    """Fetch player stats from NBA API"""
    nba_players = players.get_players()
    found_player = next((p for p in nba_players if p['full_name'].lower() == player_name.lower()), None)
    
    if not found_player:
        return None

    try:
        # Fetch career stats
        career = playercareerstats.PlayerCareerStats(player_id=found_player['id'])
        df = career.get_data_frames()[0]
        
        if df.empty:
            return None
            
        # Get most recent season data
        latest = df.iloc[-1]
        gp = float(latest['GP'])
        
        if gp == 0:
            return None
            
        # Calculate per-game stats (API returns totals)
        return {
            "id": found_player['id'],
            "full_name": found_player['full_name'],
            "stats": {
                "points_per_game": round(float(latest['PTS']) / gp, 1),
                "rebounds_per_game": round(float(latest['REB']) / gp, 1),
                "assists_per_game": round(float(latest['AST']) / gp, 1),
                "field_goal_percentage": float(latest['FG_PCT']),
                "games_played": int(gp),
                "season": latest['SEASON_ID']
            }
        }
    except Exception as e:
        print(f"Error fetching stats for {player_name}: {e}")
        return None

def get_team_info(team_name):
    """Fetch team info from NBA API"""
    nba_teams = teams.get_teams()
    found_team = next((t for t in nba_teams if t['full_name'].lower() == team_name.lower() or t['nickname'].lower() == team_name.lower()), None)
    
    if not found_team:
        return None
        
    return {
        "id": found_team['id'],
        "full_name": found_team['full_name'],
        "abbreviation": found_team['abbreviation'],
        "city": found_team['city'],
        "state": found_team['state'],
        "year_founded": found_team['year_founded']
    }

def get_all_players(limit=50):
    return [p['full_name'] for p in players.get_players()[:limit]]

def get_all_teams():
    return [t['full_name'] for t in teams.get_teams()]

def search_players_by_name(query, limit=10):
    return [p['full_name'] for p in players.get_players() if query.lower() in p['full_name'].lower()][:limit]