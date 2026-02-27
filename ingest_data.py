import chromadb
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter

# This script mimics an ETL (Extract, Transform, Load) pipeline.
# It loads raw text data into a vector database for the agent to retrieve later.

def ingest_data():
    print("Starting Advanced Data Ingestion...")

    client = chromadb.PersistentClient(path="./chroma_db")

    # Note: Chroma uses a default embedding model (all-MiniLM-L6-v2) if none is provided.
    # This runs locally and is free.
    collection = client.get_or_create_collection(name="nba_knowledge_base")
    
    # 1. EXTRACT: Load data from a file
    print("Extracting data from nba_articles.txt...")
    with open("nba_articles.txt", "r") as f:
        text_data = f.read()

    # 2. TRANSFORM: Chunk the data into smaller, more manageable pieces
    print("Transforming data (chunking)...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = text_splitter.split_text(text_data)
    ids = [f"chunk_{i}" for i in range(len(documents))]

    # 3. LOAD: Upsert the chunks into ChromaDB
    print(f"Loading {len(documents)} document chunks into ChromaDB...")
    collection.upsert(documents=documents, ids=ids)
    
    print("Successfully completed ingestion pipeline.")

if __name__ == "__main__":
    ingest_data()