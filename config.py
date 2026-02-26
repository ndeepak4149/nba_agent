import os
from dotenv import load_dotenv

load_dotenv()

# GROQ Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"

# Agent Configuration
AGENT_TEMPERATURE = 0.7
AGENT_MAX_TOKENS = 2048

# NBA Data
NBA_TEAMS = [
    "Los Angeles Lakers",
    "Boston Celtics",
    "Golden State Warriors",
    "Miami Heat",
    "Denver Nuggets",
    "Phoenix Suns",
    "New York Knicks",
    "Los Angeles Clippers"
]

# Agent Types
AGENT_TYPES = {
    "stats_analyzer": "Analyzes player and team statistics",
    "player_scout": "Evaluates player performance and potential",
    "trade_analyst": "Analyzes potential trades and their impact",
    "game_predictor": "Predicts game outcomes based on data"
}