from data import get_player_info, get_team_info, get_all_players, get_all_teams, search_players_by_name
import json

class NBATool:
    """Tools that agents can use to access NBA data"""
    
    @staticmethod
    def get_player_stats(player_name: str) -> dict:
        """Get a player's statistics"""
        player = get_player_info(player_name)
        if player:
            return {
                "success": True,
                "data": player
            }
        return {
            "success": False,
            "error": f"Player '{player_name}' not found"
        }
    
    @staticmethod
    def get_team_stats(team_name: str) -> dict:
        """Get a team's statistics"""
        team = get_team_info(team_name)
        if team:
            return {
                "success": True,
                "data": team
            }
        return {
            "success": False,
            "error": f"Team '{team_name}' not found"
        }
    
    @staticmethod
    def search_players(query: str) -> dict:
        """Search for players by name"""
        results = search_players_by_name(query, limit=10)
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    
    @staticmethod
    def list_all_teams() -> dict:
        """Get list of all NBA teams"""
        teams = get_all_teams()
        return {
            "success": True,
            "teams": teams,
            "count": len(teams)
        }
    
    @staticmethod
    def list_top_players(limit: int = 50) -> dict:
        """Get list of top NBA players"""
        players = get_all_players(limit)
        return {
            "success": True,
            "players": players,
            "count": len(players)
        }
    
    @staticmethod
    def compare_players(player1: str, player2: str) -> dict:
        """Compare two players"""
        p1 = get_player_info(player1)
        p2 = get_player_info(player2)
        
        if not p1 or not p2:
            return {
                "success": False,
                "error": "One or both players not found"
            }
        
        return {
            "success": True,
            "player1": player1,
            "player2": player2,
            "comparison": {
                "points": {
                    player1: p1["stats"]["points_per_game"],
                    player2: p2["stats"]["points_per_game"]
                },
                "rebounds": {
                    player1: p1["stats"]["rebounds_per_game"],
                    player2: p2["stats"]["rebounds_per_game"]
                },
                "assists": {
                    player1: p1["stats"]["assists_per_game"],
                    player2: p2["stats"]["assists_per_game"]
                },
                "field_goal_percentage": {
                    player1: p1["stats"]["field_goal_percentage"],
                    player2: p2["stats"]["field_goal_percentage"]
                }
            }
        }