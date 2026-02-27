from nba_api.stats.endpoints import playerdashboardbyyearoveryear, leaguedashteamstats
import time
from functools import wraps

def retry(attempts=3, delay=2):
    """
    A decorator for retrying a function call with a delay in case of exceptions.
    This makes the data fetching more resilient to temporary API or network errors.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Attempt {attempt + 1}/{attempts} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                    if attempt + 1 == attempts:
                        print(f"All {attempts} attempts failed for {func.__name__}. Returning None.")
                        return None
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(attempts=3, delay=1)
def get_player_season_stats(player_id: int):
    """
    Fetches season average statistics for a given player ID for their most recent season.
    """
    # Use PlayerDashboardByYearOverYear to get season totals/averages
    player_dashboard = playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(player_id=player_id)
    df = player_dashboard.get_data_frames()[0] # [0] is OverallPlayerDashboard
    
    if df.empty:
        return None
        
    # Get the most recent season's stats (first row)
    latest_season_stats = df.iloc[0]
    
    return {
        "season": latest_season_stats['GROUP_VALUE'],
        "games_played": int(latest_season_stats['GP']),
        "points_per_game": float(latest_season_stats['PTS']),
        "rebounds_per_game": float(latest_season_stats['REB']),
        "assists_per_game": float(latest_season_stats['AST']),
        "field_goal_percentage": float(latest_season_stats['FG_PCT']),
        "three_point_percentage": float(latest_season_stats['FG3_PCT']),
        "free_throw_percentage": float(latest_season_stats['FT_PCT']),
    }

@retry(attempts=3, delay=1)
def get_team_season_stats(team_id: int):
    """
    Fetches season average statistics for a given team ID for the current season.
    """
    # This endpoint provides stats for all teams for the season
    team_stats_dashboard = leaguedashteamstats.LeagueDashTeamStats()
    df = team_stats_dashboard.get_data_frames()[0]

    if df.empty:
        return None

    # Find the specific team's stats by its ID
    team_stats = df[df['TEAM_ID'] == team_id]
    if team_stats.empty:
        return None

    # Extract the first (and only) row of stats
    latest_team_stats = team_stats.iloc[0]

    return {
        "wins": int(latest_team_stats['W']),
        "losses": int(latest_team_stats['L']),
        "win_percentage": float(latest_team_stats['W_PCT']),
        "points_per_game": float(latest_team_stats['PTS']),
        "field_goal_percentage": float(latest_team_stats['FG_PCT']),
        "three_point_percentage": float(latest_team_stats['FG3_PCT']),
        "rebounds_per_game": float(latest_team_stats['REB']),
        "assists_per_game": float(latest_team_stats['AST']),
    }