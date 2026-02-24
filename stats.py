from langchain.tools import tool
from nba_api.stats.endpoints import commonplayerinfo, playergamelog
from nba_api.stats.static import players

@tool
def get_player_id(name: str):
    """Finds the ID for an NBA player by name."""
    nba_players = players.get_players()
    for player in nba_players:
        if player['full_name'].lower() == name.lower():
            return player['id']
    return None

@tool
def get_player_stats(name: str):
    """
    Fetches the game log (stats) for a player's current season.
    Returns a string summary of their last game.
    """
    player_id = get_player_id(name)
    if not player_id:
        return f"Error: Could not find player named {name}"

    # Get last 5 games
    gamelog = playergamelog.PlayerGameLog(player_id=player_id, season='2025-26')
    df = gamelog.get_data_frames()[0]
    
    # We only return the last game to keep it simple for now
    last_game = df.iloc[0]
    
    return (f"Stats for {name} in last game vs {last_game['MATCHUP']}:\n"
            f"Points: {last_game['PTS']}, "
            f"Rebounds: {last_game['REB']}, "
            f"Assists: {last_game['AST']}")