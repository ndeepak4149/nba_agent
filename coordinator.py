import os
import sys
from dotenv import load_dotenv
from groq import Groq
from agents import StatsAnalyzer, PlayerScout, TradeAnalyst, GamePredictor
import json

load_dotenv()

class NBACrew:
    """Main coordinator that manages all NBA agents"""
    
    def __init__(self):
        self.analyzer = StatsAnalyzer()
        self.scout = PlayerScout()
        self.trader = TradeAnalyst()
        self.predictor = GamePredictor()
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or "your_groq_api_key" in api_key:
            print("❌ ERROR: Invalid or missing GROQ_API_KEY in .env file.")
            sys.exit(1)
            
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"
        self.conversation_history = []
        
        self.agents = {
            "StatsAnalyzer": self.analyzer,
            "PlayerScout": self.scout,
            "TradeAnalyst": self.trader,
            "GamePredictor": self.predictor,
        }
        self.agent_descriptions = {
            "StatsAnalyzer": "Analyzes player or team statistics.",
            "PlayerScout": "Evaluates a player's performance, strengths, weaknesses, and potential.",
            "TradeAnalyst": "Compares two players for a potential trade.",
            "GamePredictor": "Predicts the outcome of a matchup between two teams.",
        }
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def synthesize_responses(self, task: str, responses: dict) -> str:
        """
        Synthesize responses from multiple agents into a coherent answer
        """
        synthesis_prompt = f"""You are an NBA expert synthesizing insights from multiple specialist agents.

Please synthesize these responses into a detailed, comprehensive answer that:
1. Combines insights from all agents with deep analysis.
2. Highlights the most important findings and explains the 'why' behind them.
3. Provides actionable recommendations backed by specific statistics.
4. Explains advanced concepts clearly but maintains technical depth.
5. If live stats are missing, rely on your expert knowledge of current NBA rosters and trends.

Task: {task}

Responses from specialists:
{json.dumps(responses, indent=2)}

Synthesis:"""
        messages = [
            {"role": "system", "content": "You are an expert NBA analyst synthesizing insights from multiple specialists."},
            {"role": "user", "content": synthesis_prompt}
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content

    def route_task(self, task: str) -> str:
        """Intelligently routes a task to the best agent."""
        print(f"Coordinator: Routing task '{task}'...")
        
        router_prompt = f"""
        You are the routing brain for an NBA AI system. Your goal is to map a user's request to the correct tool and extract the necessary parameters.
        
        Available Tools:
        1. evaluate_trade(player1, player2) - Analyze a trade between two players.
        2. predict_game(team1, team2) - Predict the winner of a game between two teams.
        3. scout_player(player_name) - Detailed scouting report for a player.
        4. analyze_player_comprehensive(player_name) - General stats and analysis for a player.
        5. analyze_team_comprehensive(team_name) - General team analysis (Current season only).
        6. check_live_games() - Check scores or games scheduled for today.
        7. ask_question(question) - General knowledge, historical questions, comparisons of eras, or if no other tool fits.

        User Request: "{task}"
        
        IMPORTANT: If the user asks about a specific year, historical team (e.g., '96 Bulls'), or compares eras, use 'ask_question'.
        
        Output strictly valid JSON with keys: "tool" (string) and "params" (dict).
        Example: {{"tool": "evaluate_trade", "params": {{"player1": "LeBron James", "player2": "Steph Curry"}}}}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": router_prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            routing_decision = json.loads(response.choices[0].message.content)
            tool = routing_decision.get("tool")
            params = routing_decision.get("params", {})
            
            print(f"  -> Decided to use: {tool} with {params}")

            if tool == "evaluate_trade":
                return self.evaluate_trade(params.get("player1"), params.get("player2"))
            elif tool == "predict_game":
                return self.predict_game(params.get("team1"), params.get("team2"))
            elif tool == "scout_player":
                return self.scout.scout_player(params.get("player_name"))
            elif tool == "analyze_player_comprehensive":
                return self.analyze_player_comprehensive(params.get("player_name"))
            elif tool == "analyze_team_comprehensive":
                return self.analyze_team_comprehensive(params.get("team_name"))
            elif tool == "check_live_games":
                return self.analyzer.check_live_games()
            else:
                return self.ask_question(task)
                
        except Exception as e:
            print(f"Routing Error: {e}. Falling back to general question.")
            return self.ask_question(task)

    def run(self, task: str) -> str:
        """Main entry point to run a task with the crew."""
        print(f"Executing task: {task}")
        
        # Reset agent memories to prevent context bloating and rate limits
        for agent in self.agents.values():
            agent.reset_memory()
            
        self.add_to_history("user", task)
        answer = self.route_task(task)
        self.add_to_history("assistant", answer)
        return answer
    
    def analyze_player_comprehensive(self, player_name: str) -> str:
        """Comprehensive player analysis using multiple agents"""
        print(f"Analyzing {player_name} from multiple perspectives...")
        
        responses = {}
        
        print(f"Stats Analyzer: Analyzing statistics...")
        responses["stats_analysis"] = self.analyzer.analyze_player(player_name)
        
        print(f"Player Scout: Evaluating performance...")
        responses["scout_evaluation"] = self.scout.scout_player(player_name)
        
        print(f"Synthesizing insights from all agents...")
        synthesis = self.synthesize_responses(
            f"Provide a comprehensive analysis of {player_name}",
            responses
        )
        
        return synthesis
    
    def analyze_team_comprehensive(self, team_name: str) -> str:
        """Comprehensive team analysis using multiple agents"""
        print(f"Analyzing {team_name} from multiple perspectives...")
        
        responses = {}
        
        print(f"Stats Analyzer: Analyzing team statistics...")
        responses["team_stats"] = self.analyzer.analyze_team(team_name)
        
        print(f"Synthesizing insights...")
        synthesis = self.synthesize_responses(
            f"Provide a comprehensive analysis of {team_name}",
            responses
        )
        
        return synthesis
    
    def evaluate_trade(self, player1: str, player2: str) -> str:
        """Evaluate a potential trade between two players"""
        print(f"Evaluating trade: {player1} for {player2}...")
        
        responses = {}
        
        print(f"Trade Analyst: Analyzing trade scenario...")
        responses["trade_analysis"] = self.trader.compare_for_trade(player1, player2)
        
        print(f"Scout: Evaluating player value...")
        responses["player_comparison"] = self.scout.scout_player(player1) + "\n---\n" + self.scout.scout_player(player2)
        
        print(f"Synthesizing trade insights...")
        synthesis = self.synthesize_responses(
            f"Evaluate trading {player1} for {player2}. Is this a good trade?",
            responses
        )
        
        return synthesis
    
    def predict_game(self, team1: str, team2: str) -> str:
        """Predict a game outcome with detailed analysis"""
        print(f"Predicting: {team1} vs {team2}...")
        
        responses = {}
        
        try:
            print(f"Game Predictor: Analyzing matchup...")
            responses["prediction"] = self.predictor.predict_matchup(team1, team2)
        except Exception as e:
            print(f"⚠️ Game Predictor Error: {e}")
            responses["prediction"] = "Data unavailable due to API error."

        try:
            print(f"Stats Analyzer: Analyzing both teams...")
            responses["team1_analysis"] = self.analyzer.analyze_team(team1)
            responses["team2_analysis"] = self.analyzer.analyze_team(team2)
        except Exception as e:
            print(f"⚠️ Stats Analyzer Error: {e}")
            responses["team_analysis"] = "Data unavailable due to API error."
        
        print(f"Synthesizing prediction...")
        synthesis = self.synthesize_responses(
            f"Predict the winner of {team1} vs {team2}. Consider all factors.",
            responses
        )
        
        return synthesis
    
    def ask_question(self, question: str) -> str:
        """Answer any NBA-related question using the crew"""
        print(f"Processing question: {question}")
        
        self.add_to_history("user", question)
        
        system_prompt = """You are an expert NBA analyst with access to multiple specialist agents.
        
You can analyze players, teams, predict games, and evaluate trades.
Always provide detailed, informative answers based on real NBA data.
Include statistical evidence and explain your reasoning thoroughly.
Be professional and knowledgeable."""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ] + self.conversation_history
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        answer = response.choices[0].message.content
        self.add_to_history("assistant", answer)
        
        return answer
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


def main():
    crew = NBACrew()
    
    print("=" * 60)
    print("NBA AGENT SYSTEM")
    print("=" * 60)
    print("\nCommands:")
    print("  player <name>     - Comprehensive player analysis")
    print("  team <name>       - Comprehensive team analysis")
    print("  trade <p1> <p2>   - Evaluate trade between two players")
    print("  predict <t1> <t2> - Predict game outcome")
    print("  ask <question>    - Ask any NBA question")
    print("  Ask any NBA-related question. The coordinator will route it to the best agent.")
    print("  clear             - Clear conversation history")
    print("  quit              - Exit program")
    print("\nExample:")
    print("  player LeBron James")
    print("  team Boston Celtics")
    print("  trade LeBron James Stephen Curry")
    print("  predict Lakers Celtics")
    print("  analyze LeBron James")
    print("  scout Victor Wembanyama")
    print("  trade LeBron James and Stephen Curry")
    print("  predict who will win between the Lakers and the Celtics")
    print("=" * 60 + "\n")
    
    while True:
        try:
            user_input = input("User: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("Goodbye!")
                break
            
            if user_input.lower() == "clear":
                crew.clear_history()
                print("Conversation history cleared\n")
                continue

            if user_input:
                result = crew.run(user_input)
                print(f"\nSystem:\n{result}\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()