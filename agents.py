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
        self.model = "llama-3.1-8b-instant"
        self.memory = []
        self.last_usage = None
        self.tools = NBATool()
    
    def add_to_memory(self, role: str, content: str):
        self.memory.append({
            "role": role,
            "content": content
        })

    def reset_memory(self):
        self.memory = []
        self.last_usage = None

    def get_last_usage(self):
        """Returns the token usage from the last non-streaming API call."""
        return self.last_usage
    
    def get_system_prompt(self) -> str:
        return f"""You are {self.name}, an NBA AI agent with the role: {self.role}
        
You have access to real NBA data including player stats, team information, and player comparisons.
When asked questions about NBA, provide detailed, informative answers.
If the provided context contains specific stats, prioritize them.
If the context is missing stats (Lite Mode), USE YOUR INTERNAL KNOWLEDGE about current rosters, player strengths, and team dynamics to provide the best possible analysis.
Be professional, knowledgeable, and helpful.
If you don't have information about something, say so clearly."""
    
    def think(self, query: str, stream: bool = False):
        self.add_to_memory("user", query)
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ] + self.memory
        
        if stream:
            self.last_usage = None # Usage tracking is not straightforward with streams
            response_stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True
            )
            # Return a generator that also captures the full response for memory
            def stream_and_capture():
                full_response = []
                for chunk in response_stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response.append(content)
                        yield content
                # After streaming, add the complete message to memory
                self.add_to_memory("assistant", "".join(full_response))
            return stream_and_capture()
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=False
            )
            self.last_usage = response.usage
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
        player_info = self.tools.get_player_stats(player_name)
        
        if not player_info["success"]:
            return player_info["error"]
        
        data = json.dumps(player_info["data"], indent=2)
        query = f"Analyze this player's stats and provide detailed insights with explanations:\n{data}"
        
        return self.think(query)
    
    def analyze_team(self, team_name: str) -> str:
        team_info = self.tools.get_team_stats(team_name)
        
        if not team_info["success"]:
            return team_info["error"]
        
        data = json.dumps(team_info["data"], indent=2)
        query = f"Analyze this team's performance based on the provided data. If specific stats/roster are missing (Lite Mode), provide a general assessment of the team's status and history:\n{data}"
        
        return self.think(query)
    
    def check_live_games(self) -> str:
        games_info = self.tools.get_games_today()
        
        if not games_info["success"]:
            return "Failed to fetch live games."
            
        data = json.dumps(games_info["games"], indent=2)
        query = f"Report on the NBA games happening today based on this data:\n{data}"
        return self.think(query)

class PlayerScout(BaseAgent):
    """Agent specialized in player evaluation"""
    
    def __init__(self):
        super().__init__(
            name="Player Scout",
            role="Evaluate player performance and potential"
        )
    
    def scout_player(self, player_name: str) -> str:
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
        query = f"Predict the outcome of this matchup. If specific stats are provided, use them. If not, rely on your knowledge of the teams' current rosters and playing styles:\n{data_str}"
        
        return self.think(query)

class DraftProspect(BaseAgent):
    """Agent specialized in scouting NBA draft prospects"""

    def __init__(self):
        super().__init__(
            name="Draft Prospect Scout",
            role="Evaluate the potential of NBA draft prospects based on available public information."
        )

    def scout_prospect(self, prospect_name: str) -> str:
        """Scouts a draft prospect using web search."""
        search_result = self.tools.web_search(f"NBA draft prospect {prospect_name}")

        if not search_result["success"]:
            return search_result["error"]

        context = search_result["result"]
        query = f"As a professional NBA scout, provide a detailed scouting report for the draft prospect '{prospect_name}' based on the following information. Analyze their strengths, weaknesses, NBA potential, and a potential player comparison if possible.\n\nContext:\n{context}"
        return self.think(query)

class Reviewer(BaseAgent):
    """Agent specialized in reviewing and improving final answers."""

    def __init__(self):
        super().__init__(
            name="Answer Reviewer",
            role="Critique and refine draft answers to ensure they are accurate, well-structured, and meet a high standard of quality."
        )

    def review_answer(self, task: str, draft_answer: str, stream: bool = False):
        """Reviews a draft answer and provides a final, polished version."""
        
        query = f"""
        The user's original task was: "{task}"

        Here is the draft answer generated by the agent crew:
        ---
        {draft_answer}
        ---

        Please review this draft. Your goal is to act as a final quality gate.
        1.  **Clarity and Conciseness**: Is the answer easy to understand? Can it be made more direct without losing key information?
        2.  **Tone**: Is the tone professional and analytical, as expected from an expert?
        3.  **Completeness**: Does the answer fully address the user's original task?
        4.  **Formatting**: Use markdown (like bullet points or bold text) to improve readability.

        Your final output must ONLY be the refined answer itself. Do not include any preamble, meta-commentary, or explanation of the changes you made.
        """
        
        return self.think(query, stream=stream)