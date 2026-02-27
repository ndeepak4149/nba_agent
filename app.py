import streamlit as st
from dotenv import load_dotenv
from coordinator import NBACrew

load_dotenv()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "nba_crew" not in st.session_state:
    st.session_state.nba_crew = NBACrew()

st.title("🏀 NBA AI Crew")
st.caption("Powered by a Custom Multi-Agent System")

with st.sidebar:
    st.header("Controls")
    if st.button("Clear Conversation History"):
        st.session_state.messages = []
        st.session_state.nba_crew.clear_history()
        st.rerun()

# --- UI Interaction ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_query := st.chat_input("Ask a question about the NBA:"):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.spinner("The Crew is on the job..."):
        final_answer_stream, agent_process_log = st.session_state.nba_crew.run(user_query, stream=True)

        with st.chat_message("assistant"):
            # Use write_stream to display the response as it comes in.
            # It conveniently returns the full response string once the stream is done.
            final_answer = st.write_stream(final_answer_stream)
        
        st.session_state.nba_crew.add_to_history("assistant", final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

        with st.expander("Copy Full Response"):
            st.code(final_answer, language=None)
        
        with st.expander("Show Agent Process Log"):
            for log_entry in agent_process_log:
                level = log_entry.get("level", "INFO").upper()
                message = log_entry.get("message", "")
                if level == "ERROR":
                    st.error(message)
                elif level == "WARN":
                    st.warning(message)
                elif level == "SUMMARY":
                    st.success(message)
                else:
                    st.info(message)