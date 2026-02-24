from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import tool

@tool
def search_web(query: str):
    """
    Searches Wikipedia for general information, history, or biography.
    Useful for finding out who a player is, who they play for, or coach info.
    """
    # We limit it to the top 1 result to keep it fast
    api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=1000)
    wiki = WikipediaQueryRun(api_wrapper=api_wrapper)
    return wiki.run(query)