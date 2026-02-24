import os
from dotenv import load_dotenv
from groq import Groq
from tools import NBATool
import json

load_dotenv()

class BaseAgent:
    """Base class for all NBA agents"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.memory = []  # Store conversation history
        self.tools = NBATool()
    
    def add_to_memory(self, role: str, content: str):
        """Add a message to memory"""
        self.memory.append({
            "role": role,
            "content": content
        })
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are {self.name}, an NBA AI agent with the role: {self.role}
        
You have access to real NBA data including player stats, team information, and player comparisons.
When asked questions about NBA, provide detailed, informative answers based on the available data.
Be professional, knowledgeable, and helpful.
If you don't have information about something, say so clearly."""
    
    def think(self, query: str) -> str:
        """Think about a query and provide a response"""
        self.add_to_memory("user", query)
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ] + self.memory
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        
        answer = response.choices[0].message.content
        self.add_to_memory("assistant", answer)
        
        return answer

class StatsAnalyzer(BaseAgent):
    """Agent specialized in analyzing player and team statistics"""
    
    def __init__(self):
        super().__init__(
            name="Stats Analyzer",
            role="Analyze and interpret NBA player and team statistics"
        )
    
    def analyze_player(self, player_name: str) -> str:
        """Analyze a specific player"""
        player_info = self.tools.get_player_stats(player_name)
        
        if not player_info["success"]:
            return player_info["error"]
        
        data = json.dumps(player_info["data"], indent=2)
        query = f"Analyze this player's stats and provide detailed insights with explanations:\n{data}"
        
        return self.think(query)
    
    def analyze_team(self, team_name: str) -> str:
        """Analyze a specific team"""
        team_info = self.tools.get_team_stats(team_name)
        
        if not team_info["success"]:
            return team_info["error"]
        
        data = json.dumps(team_info["data"], indent=2)
        query = f"Analyze this team's performance in detail, explaining key strengths and weaknesses:\n{data}"
        
        return self.think(query)

class PlayerScout(BaseAgent):
    """Agent specialized in player evaluation"""
    
    def __init__(self):
        super().__init__(
            name="Player Scout",
            role="Evaluate player performance and potential"
        )
    
    def scout_player(self, player_name: str) -> str:
        """Scout a player"""
        player_info = self.tools.get_player_stats(player_name)
        
        if not player_info["success"]:
            return player_info["error"]
        
        data = json.dumps(player_info["data"], indent=2)
        query = f"As a scout, provide a comprehensive and detailed evaluation of this player's potential and performance, explaining your reasoning:\n{data}"
        
        return self.think(query)

class TradeAnalyst(BaseAgent):
    """Agent specialized in analyzing trades"""
    
    def __init__(self):
        super().__init__(
            name="Trade Analyst",
            role="Analyze potential trades and their impact"
        )
    
    def compare_for_trade(self, player1: str, player2: str) -> str:
        """Compare two players for a potential trade"""
        comparison = self.tools.compare_players(player1, player2)
        
        if not comparison["success"]:
            return comparison["error"]
        
        data = json.dumps(comparison, indent=2)
        query = f"Analyze this potential trade scenario in detail, explaining the pros and cons for both sides:\n{data}"
        
        return self.think(query)

class GamePredictor(BaseAgent):
    """Agent specialized in game predictions"""
    
    def __init__(self):
        super().__init__(
            name="Game Predictor",
            role="Predict game outcomes based on team and player data"
        )
    
    def predict_matchup(self, team1: str, team2: str) -> str:
        """Predict a game outcome between two teams"""
        team1_info = self.tools.get_team_stats(team1)
        team2_info = self.tools.get_team_stats(team2)
        
        if not team1_info["success"] or not team2_info["success"]:
            return "One or both teams not found"
        
        data = {
            "matchup": f"{team1} vs {team2}",
            team1: team1_info["data"],
            team2: team2_info["data"]
        }
        
        data_str = json.dumps(data, indent=2)
        query = f"Predict the outcome of this matchup based on the statistics, providing a detailed explanation of the factors involved:\n{data_str}"
        
        return self.think(query)