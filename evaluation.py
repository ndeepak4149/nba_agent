import json
import os
import sys
from dotenv import load_dotenv
from groq import Groq
from coordinator import NBACrew

load_dotenv()

EVALUATION_SET_FILE = "evaluation_set.json"

def create_evaluation_set():
    """Creates a sample evaluation set if it doesn't exist."""
    if not os.path.exists(EVALUATION_SET_FILE):
        print("Creating sample evaluation_set.json...")
        eval_set = [
            {
                "task": "Who won the 2024 NBA championship?",
                "expected_keywords": ["Boston Celtics", "Jaylen Brown"],
                "eval_criteria": "Answer must correctly identify the Boston Celtics as the winner."
            },
            {
                "task": "Compare LeBron James and Michael Jordan",
                "expected_keywords": ["rings", "era", "playstyle", "stats"],
                "eval_criteria": "Answer should be a balanced comparison, mentioning different eras and strengths. It should not definitively declare one as 'better' without qualification."
            },
            {
                "task": "What are the stats for player 'Nonexistent Player'?",
                "expected_keywords": ["not found", "could not find"],
                "eval_criteria": "Agent must gracefully handle a non-existent player and state that the player was not found."
            }
        ]
        with open(EVALUATION_SET_FILE, 'w') as f:
            json.dump(eval_set, f, indent=2)

def run_evaluation():
    """Runs the agent against the evaluation set and gets scores from an LLM judge."""
    create_evaluation_set()

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    nba_crew = NBACrew()

    with open(EVALUATION_SET_FILE, 'r') as f:
        evaluation_set = json.load(f)

    print("--- Starting AI Evaluation ---")
    all_scores = []
    for i, item in enumerate(evaluation_set):
        task = item["task"]
        print(f"\n[{i+1}/{len(evaluation_set)}] Running task: {task}")

        agent_response, _ = nba_crew.run(task, stream=False)
        print(f"  -> Agent Response: {agent_response[:100]}...")

        judge_prompt = f"""
        You are an evaluation judge. Your task is to score an AI agent's response based on a given criteria.
        Provide a score from 1 (bad) to 5 (excellent) and a brief justification.

        Task: "{task}"
        Evaluation Criteria: "{item['eval_criteria']}"
        Agent's Response: "{agent_response}"

        Output a JSON object with "score" (int) and "justification" (str).
        """

        judge_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        evaluation = json.loads(judge_response.choices[0].message.content)
        score = evaluation.get('score', 0)
        all_scores.append(score)
        print(f"  -> Judge's Score: {score}/5")
        print(f"  -> Justification: {evaluation.get('justification')}")

    print("\n--- Evaluation Summary ---")
    min_score = min(all_scores) if all_scores else 0
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    print(f"Average Score: {avg_score:.2f}/5")
    print(f"Minimum Score: {min_score}/5")

if __name__ == "__main__":
    run_evaluation()