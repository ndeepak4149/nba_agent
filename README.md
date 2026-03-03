NBA AI Crew - Comprehensive Project Overview

Project Description
NBA AI Crew is a sophisticated multi-agent AI system built with Python that leverages the power of large language models to povide expert-level NBA analysis and insights. The system uses Groq's LLM API and Streamlit to deliver an interactive conversational interface where users can ask NBA-related questions and receive detailed, professional analyses.

Data Sources:
1. NBA-API (nba_api library) 
     Source: https://github.com/swar/nba_api
     Data: Official NBA statistics from NBA from the 1946-47 season to 2023-2024 season. 
2. Wikipedia API
     Source: https://en.wikipedia.org/w/api.php
     Data: General NBA information, player bios

Key Features

1. Multi-Agent Architecture
The project implements a specialized agent system, each with a distinct role:

Stats Analyzer - Analyzes player and team statistics, providing detailed performance insights and live game reporting
Player Scout - Evaluates player potential and performance with comprehensive scouting reports
Trade Analyst - Analyzes potential trades and player comparisons to evaluate trade scenarios
Game Predictor - Predicts game outcomes based on team and player data
Draft Prospect Scout - Evaluates NBA draft prospects using web search capabilities
Answer Reviewer - Ensures final responses are accurate, well-structured, and of high quality

2. Core Technologies
LLM Integration: Groq API with Llama 3.1 8B Instant model for fast, efficient inference
Web Framework: Streamlit for interactive chat-based UI
Data Management: ChromaDB for vector storage and retrieval
Web Search: Capability to search and gather information about draft prospects
Memory Management: Conversation history tracking for context-aware responses

3. Main Components
*app.py - User Interface
  Streamlit-based web interface
  Chat interface with message history
  Real-time streaming responses from agents
  Agent process logging for transparency
  Clear conversation history feature

*agents.py - Agent Implementations
  BaseAgent class providing foundational agent functionality
  System prompts that guide agent behavior
  Memory management for conversation context
  Specialized agent classes for different NBA analysis tasks
  Support for both streaming and non-streaming responses

*coordinator.py - Agent Orchestration
  NBACrew class that coordinates multi-agent interactions
  Routes user queries to appropriate agents
  Manages agent memory and conversation flow
  Aggregates results from multiple agents

*tools.py - NBA Data Tools
  Interfaces with NBA API for player statistics
  Retrieves team information and performance data
  Implements player comparison functionality
  Fetches live game data
  Web search capabilities for draft prospects

*cache.py - Caching System
  Implements caching to reduce redundant API calls
  Improves response times for frequently asked questions

*config.py - Configuration Management
  Centralized configuration for API keys and settings
  Model selection and parameters
  Environment variable management

*data.py - Data Processing
  Handles data formatting and processing
  Prepares data for agent analysis

*evaluation.py - Performance Evaluation
  Evaluates agent responses
  Tracks performance metrics
  

How It Works:
User Input: Users ask questions about NBA through the Streamlit interface
Agent Selection: The coordinator determines which agent(s) are best suited for the question
Data Retrieval: Agents fetch relevant NBA data using available tools
Analysis: Agents use the Groq LLM to analyze data and generate insights
Response Streaming: Responses are streamed to the user in real-time
Quality Review: The Reviewer agent ensures the response meets quality standards



Installation & Setup:

Requirements:
streamlit>=1.35.0
langchain-community
groq
python-dotenv
nba_api
wikipedia
chromadb

Environment Variables
Create a .env file with: GROQ_API_KEY=your groq api key (free to use)
TAVILY_API_KEY=your tavily api key (free to use)
DATA_MODE="FULL"

BUILD AND RUN DOCKER CONTAINER

docker build -t nba-agent .

docker run -p 8501:8501 --env-file .env nba-agent








