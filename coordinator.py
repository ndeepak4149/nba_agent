import os
import sys
from dotenv import load_dotenv
from groq import Groq
from agents import StatsAnalyzer, PlayerScout, TradeAnalyst, GamePredictor, DraftProspect, Reviewer
from tools import NBATool
import json
import chromadb

load_dotenv()

class NBACrew:
    """Main coordinator that manages all NBA agents"""
    
    def __init__(self):
        self.analyzer = StatsAnalyzer()
        self.scout = PlayerScout()
        self.trader = TradeAnalyst()
        self.predictor = GamePredictor()
        self.draft_scout = DraftProspect()
        self.reviewer = Reviewer()
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or "your_groq_api_key" in api_key:
            print("❌ ERROR: Invalid or missing GROQ_API_KEY in .env file.")
            sys.exit(1)
            
        self.client = Groq(api_key=api_key)
        self.tools = NBATool()
        self.model = "llama-3.1-8b-instant"
        self.conversation_history = []
        self.log = []
        self.run_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        self.agents = {
            "StatsAnalyzer": self.analyzer,
            "PlayerScout": self.scout,
            "TradeAnalyst": self.trader,
            "GamePredictor": self.predictor,
            "DraftProspect": self.draft_scout,
            "Reviewer": self.reviewer,
        }
        self.agent_descriptions = {
            "StatsAnalyzer": "Analyzes player or team statistics.",
            "PlayerScout": "Evaluates a player's performance, strengths, weaknesses, and potential.",
            "TradeAnalyst": "Compares two players for a potential trade.",
            "GamePredictor": "Predicts the outcome of a matchup between two teams.",
            "DraftProspect": "Scouts and evaluates upcoming NBA draft prospects who are not yet in the league.",
        }
        
        self.tool_dispatch = {
            "evaluate_trade": self.evaluate_trade,
            "predict_game": self.predict_game,
            "scout_player": self._scout_player_with_usage,
            "analyze_player_comprehensive": self.analyze_player_comprehensive,
            "analyze_team_comprehensive": self.analyze_team_comprehensive,
            "check_live_games": self._check_live_games_with_usage,
            "scout_prospect": self._scout_prospect_with_usage,
            "query_knowledge_base": self.query_knowledge_base,
            "web_search": self._web_search_wrapper,
            "ask_question": self.ask_question,
        }

    def _log(self, message: str, level: str = "INFO"):
        """Adds a structured log entry."""
        self.log.append({"level": level, "message": message})

    def _log_usage(self, usage):
        """Aggregates token usage from an API response."""
        if usage:
            self.run_usage["prompt_tokens"] += usage.prompt_tokens
            self.run_usage["completion_tokens"] += usage.completion_tokens
            self.run_usage["total_tokens"] += usage.total_tokens
    
    def _scout_player_with_usage(self, player_name: str):
        result = self.scout.scout_player(player_name)
        self._log_usage(self.scout.get_last_usage())
        return result

    def _check_live_games_with_usage(self, **kwargs):
        result = self.analyzer.check_live_games()
        self._log_usage(self.analyzer.get_last_usage())
        return result

    def _scout_prospect_with_usage(self, prospect_name: str):
        result = self.draft_scout.scout_prospect(prospect_name)
        self._log_usage(self.draft_scout.get_last_usage())
        return result

    def _web_search_wrapper(self, query: str):
        search_result = self.tools.web_search(query)
        return search_result.get("result", search_result.get("error", "Web search failed."))

    def add_to_history(self, role: str, content: str):
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
        self._log_usage(response.usage)
        return response.choices[0].message.content

    def query_knowledge_base(self, query: str) -> str:
        """Queries the local vector database for specific information."""
        self._log(f"Querying knowledge base for: '{query}'")
        try:
            client = chromadb.PersistentClient(path="./chroma_db")
            collection = client.get_collection(name="nba_knowledge_base")
            results = collection.query(query_texts=[query], n_results=2)
            
            if results['documents'] and results['documents'][0]:
                return "\n".join(results['documents'][0])
            return "No relevant information found in the knowledge base."
        except Exception as e:
            self._log(f"Knowledge base query failed: {e}", level="ERROR")
            return "Error accessing the knowledge base."

    def route_task(self, task: str) -> str:
        """Intelligently routes a task to the best agent."""
        self._log(f"Routing task '{task}'...")

        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])
        
        router_prompt = f"""
        You are the routing brain for an NBA AI system. Your goal is to map the user's LATEST request to the correct tool, considering the CONVERSATION HISTORY for context.

        CONVERSATION HISTORY:
        {history_str}

        LATEST USER REQUEST: "{task}" 
        
        Available Tools: {json.dumps(list(self.tool_dispatch.keys()), indent=2)}

        IMPORTANT: Based on the LATEST USER REQUEST and the CONVERSATION HISTORY, decide which tool to use. If the latest request is a follow-up (e.g., "what about him?", "compare him to..."), use the history to understand the context (e.g., who "him" refers to). Use `scout_prospect` for players not in the NBA and `scout_player` for current NBA players. Prioritize `query_knowledge_base` for questions about the 2024 season winners and awards. Use `web_search` for broader historical questions.
        
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
            self._log_usage(response.usage)
            
            routing_decision = json.loads(response.choices[0].message.content)
            tool = routing_decision.get("tool")
            params = routing_decision.get("params", {})
            
            self._log(f"Router decided to use: {tool} with {params}")

            # Use the dispatch table to execute the correct tool
            tool_function = self.tool_dispatch.get(tool)
            
            if tool_function:
                # Unpack the params dictionary into keyword arguments
                return tool_function(**params)
            else:
                self._log(f"Unknown tool '{tool}' decided by router. Falling back.", level="WARN")
                return self.ask_question(task)
                
        except Exception as e:
            self._log(f"Routing Error: {e}. Falling back to general question.", level="ERROR")
            return self.ask_question(task)

    def is_task_on_topic(self, task: str) -> bool:
        """Uses an LLM to quickly check if the task is related to the NBA."""
        self._log("Checking if task is on-topic...")
        
        guardrail_prompt = f"""
        You are a topic classification guardrail. Your only job is to determine if the user's request is about the sport of basketball (NBA, players, teams, history, rules, etc.).

        User request: "{task}"

        Is this request about basketball? Answer with a single word: "yes" or "no".
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant", # Use a fast model
                messages=[{"role": "user", "content": guardrail_prompt}],
                temperature=0.0,
                max_tokens=5
            )
            decision = response.choices[0].message.content.strip().lower()
            return "yes" in decision
        except Exception:
            return True # Fail open if the guardrail has an error

    def run(self, task: str, stream: bool = False):
        """Main entry point to run a task with the crew."""
        self.run_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.log = [] # Reset log for each run
        self._log(f"Executing task: {task}")
        
        # Reset agent memories to prevent context bloating and rate limits
        for agent in self.agents.values():
            agent.reset_memory()

        if not self.is_task_on_topic(task):
            off_topic_response = "I am an NBA-specialized AI assistant. I can only answer questions related to basketball."
            self._log(f"Task is off-topic. Responding: '{off_topic_response}'", level="WARN")
            
            # For non-streamed edge cases, we wrap the response in a simple generator
            def generator():
                yield off_topic_response
            return generator(), self.log
            
        self.add_to_history("user", task)
        draft_answer = self.route_task(task)
        
        self._log("Reviewer: Reviewing final answer for quality and clarity.")
        final_output = self.reviewer.review_answer(task, draft_answer, stream=stream)
        self._log_usage(self.reviewer.get_last_usage())
        
        self._log("Usage for streaming Reviewer agent is not tracked.", level="WARN")
        self._log(f"Run complete. Total tracked tokens: {self.run_usage['total_tokens']} (Prompt: {self.run_usage['prompt_tokens']}, Completion: {self.run_usage['completion_tokens']})", level="SUMMARY")
        
        if stream:
            # The UI layer is responsible for adding the final answer to history after streaming
            return final_output, self.log
        else:
            # We have the final string, add it to history now
            final_answer_string = final_output
            self.add_to_history("assistant", final_answer_string)
            return final_answer_string, self.log
    
    def analyze_player_comprehensive(self, player_name: str) -> str:
        self._log(f"Analyzing {player_name} from multiple perspectives...")
        
        responses = {}
        
        self._log(f"Stats Analyzer: Analyzing statistics...")
        responses["stats_analysis"] = self.analyzer.analyze_player(player_name)
        self._log_usage(self.analyzer.get_last_usage())
        
        self._log(f"Player Scout: Evaluating performance...")
        responses["scout_evaluation"] = self.scout.scout_player(player_name)
        self._log_usage(self.scout.get_last_usage())
        
        self._log(f"Synthesizing insights from all agents...")
        synthesis = self.synthesize_responses(
            f"Provide a comprehensive analysis of {player_name}",
            responses
        )
        
        return synthesis
    
    def analyze_team_comprehensive(self, team_name: str) -> str:
        self._log(f"Analyzing {team_name} from multiple perspectives...")
        
        responses = {}
        
        self._log(f"Stats Analyzer: Analyzing team statistics...")
        responses["team_stats"] = self.analyzer.analyze_team(team_name)
        self._log_usage(self.analyzer.get_last_usage())
        
        self._log(f"Synthesizing insights...")
        synthesis = self.synthesize_responses(
            f"Provide a comprehensive analysis of {team_name}",
            responses
        )
        
        return synthesis
    
    def evaluate_trade(self, player1: str, player2: str) -> str:
        self._log(f"Evaluating trade: {player1} for {player2}...")
        
        responses = {}
        
        self._log(f"Trade Analyst: Analyzing trade scenario...")
        responses["trade_analysis"] = self.trader.compare_for_trade(player1, player2)
        self._log_usage(self.trader.get_last_usage())
        
        self._log(f"Scout: Evaluating player value...")
        p1_scout = self.scout.scout_player(player1)
        self._log_usage(self.scout.get_last_usage())
        p2_scout = self.scout.scout_player(player2)
        self._log_usage(self.scout.get_last_usage())
        responses["player_comparison"] = p1_scout + "\n---\n" + p2_scout
        
        self._log(f"Synthesizing trade insights...")
        synthesis = self.synthesize_responses(
            f"Evaluate trading {player1} for {player2}. Is this a good trade?",
            responses
        )
        
        return synthesis
    
    def predict_game(self, team1: str, team2: str) -> str:
        self._log(f"Predicting: {team1} vs {team2}...")
        
        responses = {}
        
        try:
            self._log(f"Game Predictor: Analyzing matchup...")
            responses["prediction"] = self.predictor.predict_matchup(team1, team2)
            self._log_usage(self.predictor.get_last_usage())
        except Exception as e:
            self._log(f"⚠️ Game Predictor Error: {e}", level="ERROR")
            responses["prediction"] = "Data unavailable due to API error."

        try:
            self._log(f"Stats Analyzer: Analyzing both teams...")
            responses["team1_analysis"] = self.analyzer.analyze_team(team1); self._log_usage(self.analyzer.get_last_usage())
            responses["team2_analysis"] = self.analyzer.analyze_team(team2); self._log_usage(self.analyzer.get_last_usage())
        except Exception as e:
            self._log(f"⚠️ Stats Analyzer Error: {e}", level="ERROR")
            responses["team_analysis"] = "Data unavailable due to API error."
        
        self._log(f"Synthesizing prediction...")
        synthesis = self.synthesize_responses(
            f"Predict the winner of {team1} vs {team2}. Consider all factors.",
            responses
        )
        
        return synthesis
    
    def ask_question(self, question: str) -> str:
        self._log(f"Processing general question: {question}")
        
        system_prompt = """You are an expert NBA analyst. Answer the user's question based on the provided conversation history and your general knowledge.
Provide detailed, informative answers.
Include statistical evidence and explain your reasoning thoroughly. Be professional and knowledgeable."""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ] + self.conversation_history
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        self._log_usage(response.usage)
        # The run() method is responsible for adding the final, reviewed answer to history.
        return response.choices[0].message.content
    
    def clear_history(self):
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
                result, logs = crew.run(user_input, stream=False)
                print("\n--- Agent Log ---")
                for log_entry in logs:
                    print(f"[{log_entry['level']}] {log_entry['message']}")
                print("--- End Log ---\n")
                
                print(f"System:\n{result}\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()