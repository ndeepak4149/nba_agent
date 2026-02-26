import streamlit as st
from dotenv import load_dotenv
import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
import chromadb
from config import GROQ_MODEL
import json
from tools import NBATool

# Load environment variables from .env file
load_dotenv()

# --- 1. LLMOps: Observability Setup ---
# Launch Phoenix locally to visualize traces (inputs, outputs, latency)
# This runs a local server usually at http://localhost:6006
if "phoenix_session" not in st.session_state:
    session = px.launch_app()
    st.session_state["phoenix_session"] = session
    # Instrument LangChain to automatically send traces to Phoenix
    tracer_provider = register()
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🏀 NBA AI Agent (Engineered)")
st.caption("Powered by LangChain, ChromaDB, and Arize Phoenix")

# --- 2. RAG Tool Setup (Long-Term Memory) ---
@tool
def query_nba_knowledge_base(query: str) -> str:
    """Retrieves specific NBA facts from the local vector database. Use for answering questions about recent NBA championships, MVPs, and awards. Good for historical facts and awards."""
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="nba_knowledge_base")
    results = collection.query(query_texts=[query], n_results=1)
    
    if results['documents'] and results['documents'][0]:
        return results['documents'][0][0]
    return "No relevant data found in knowledge base."

@tool
def compare_players(players_str: str) -> str:
    """Use to compare the stats of two NBA players. Input must be a comma-separated string of two player names, e.g., 'LeBron James, Stephen Curry'."""
    try:
        parts = players_str.split(',')
        if len(parts) < 2:
            return json.dumps({"success": False, "error": "Input must be two player names separated by a comma."})
        player1 = parts[0].strip()
        player2 = parts[1].strip()
        result = NBATool.compare_players(player1=player1, player2=player2)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": f"An error occurred while parsing player names: {str(e)}"})

@tool
def get_player_stats(player_name: str) -> str:
    """Use to get detailed statistics for a single, specific NBA player. Input should be the player's full name."""
    return json.dumps(NBATool.get_player_stats(player_name), indent=2)

@tool
def get_team_stats(team_name: str) -> str:
    """Use to get statistics for a single, specific NBA team. Input should be the team's full name, e.g., 'Los Angeles Lakers'."""
    return json.dumps(NBATool.get_team_stats(team_name), indent=2)

@tool
def web_search(query: str) -> str:
    """A fallback tool for current events, game schedules, or information not found in other specialized tools."""
    return TavilySearchResults(max_results=3).run(query)

# Define Tools
tools = [
    compare_players,
    get_player_stats,
    get_team_stats,
    query_nba_knowledge_base,
    web_search,
]

# --- 3. Agent Initialization ---
# We are switching to a modern, more token-efficient tool-calling agent.
# This is more robust than the older ReAct agent and avoids prompt size errors.
llm = ChatGroq(model=GROQ_MODEL, temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful and knowledgeable NBA assistant. You have access to several tools to answer questions."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

tool_calling_agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=tool_calling_agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

def get_detailed_analysis(user_query: str, result: dict, llm: ChatGroq) -> str:
    """
    Synthesizes a detailed response from the agent's output, either from tool usage
    or by expanding on a direct answer.
    """
    intermediate_steps = result.get("intermediate_steps", [])

    if intermediate_steps:
        with st.spinner("Synthesizing a detailed analysis..."):
            tool_outputs = "\n\n".join(
                [
                    f"Tool: {action.tool}\nInput: {action.tool_input}\nOutput: {observation}"
                    for action, observation in intermediate_steps
                ]
            )

            synthesis_prompt = f"""
You are an expert NBA analyst. Your task is to synthesize the findings from various tools into a single, comprehensive, and insightful response.
The user asked: "{user_query}"

The following information was gathered by specialist tools:
{tool_outputs}

Based on the data above, provide a deep and detailed analysis that addresses the user's question.
- Explain your reasoning step-by-step.
- If you are comparing players or teams, highlight key statistical differences and what they mean in a game context.
- Do not just repeat the data; interpret it and explain the 'why' behind the numbers.
- Conclude with a clear summary of your findings.
- Your tone should be that of a professional sports analyst.
"""
            synthesis_response = llm.invoke(synthesis_prompt)
            return synthesis_response.content
    else:
        with st.spinner("Expanding on the initial answer..."):
            initial_answer = result.get("output")
            synthesis_prompt = f"""
You are an expert NBA analyst. A user asked a question and you provided an initial, brief answer. Now, expand on that answer with deep analysis and reasoning.

User's Question: "{user_query}"
Your Initial Answer: "{initial_answer}"

Now, provide a more comprehensive and insightful response based on your internal knowledge.
- Elaborate on your initial points.
- Provide context, history, or statistical evidence to support your claims.
- Explain the 'why' behind your answer.
- Your tone should be that of a professional sports analyst.
"""
            synthesis_response = llm.invoke(synthesis_prompt)
            return synthesis_response.content

# --- 4. UI Interaction ---
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_query := st.chat_input("Ask a question about the NBA:"):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.spinner("Thinking... (Check Phoenix UI for traces)"):
        agent_input = {
            "input": user_query,
            "chat_history": [
                (msg["role"], msg["content"]) for msg in st.session_state.messages
            ],
        }
        result = agent_executor.invoke(agent_input)

        intermediate_steps = result.get("intermediate_steps", [])

        final_answer = get_detailed_analysis(user_query, result, llm)

        with st.chat_message("assistant"):
            st.markdown(final_answer)
        
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

        # Add a copyable version of the output for convenience
        with st.expander("Copy Full Response"):
            st.code(final_answer, language=None)

        # Display the analytics in an expander
        if intermediate_steps:
            with st.expander("Show Raw Analytics and Agent Steps"):
                st.subheader("Agent's Thought Process")
                for i, (action, observation) in enumerate(intermediate_steps):
                    st.markdown(f"**Step {i+1}: Tool Call**")
                    st.info(f"Agent used tool: `{action.tool}` with input: `{action.tool_input}`")
                    
                    st.markdown("**Analytics / Tool Output:**")
                    try:
                        analytics_data = json.loads(observation)
                        st.json(analytics_data)
                    except (json.JSONDecodeError, TypeError):
                        st.text(observation)

    with st.expander("See Engineering Details"):
        st.info("View the 'Phoenix' tab in your browser (localhost:6006) to see the full trace of this execution.")