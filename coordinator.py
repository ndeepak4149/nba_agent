"""
NBA Agent Coordinator - Orchestrates multiple agents to work together
"""
import os
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
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
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

        task_lower = task.lower()
        if "trade" in task_lower or "compare" in task_lower:
            players = task_lower.replace("trade", "").replace("compare", "").replace(" for ", " and ").split(" and ")
            player1 = players[0].strip() if len(players) > 0 else ""
            player2 = players[1].strip() if len(players) > 1 else ""
            if player1 and player2:
                return self.evaluate_trade(player1, player2)
        elif "predict" in task_lower or " vs " in task_lower:
            teams = task_lower.replace("predict", "").replace("who will win between the", "").replace(" and the", " vs ").split(" vs ")
            team1 = teams[0].strip() if len(teams) > 0 else ""
            team2 = teams[1].strip() if len(teams) > 1 else ""
            if team1 and team2:
                return self.predict_game(team1, team2)
        elif "scout" in task_lower or "potential" in task_lower:
            player_name = task_lower.replace("scout", "").replace("potential of", "").strip()
            return self.scout.scout_player(player_name)
        elif "stats" in task_lower or "analyze" in task_lower or "how good is" in task_lower:
            entity_name = task_lower.replace("stats for", "").replace("analyze", "").replace("how good is", "").strip()
            return self.analyze_player_comprehensive(entity_name)

        return self.ask_question(task)

    def run(self, task: str) -> str:
        """Main entry point to run a task with the crew."""
        print(f"Executing task: {task}")
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
        
        print(f"Game Predictor: Analyzing matchup...")
        responses["prediction"] = self.predictor.predict_matchup(team1, team2)
        
        print(f"Stats Analyzer: Analyzing both teams...")
        responses["team1_analysis"] = self.analyzer.analyze_team(team1)
        responses["team2_analysis"] = self.analyzer.analyze_team(team2)
        
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


# Interactive CLI for testing
def main():
    """Main function for interactive testing"""
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