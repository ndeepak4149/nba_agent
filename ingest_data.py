import chromadb
import os

# This script mimics an ETL (Extract, Transform, Load) pipeline.
# It loads raw text data into a vector database for the agent to retrieve later.

def ingest_data():
    print("Starting Data Ingestion...")

    client = chromadb.PersistentClient(path="./chroma_db")

    # Note: Chroma uses a default embedding model (all-MiniLM-L6-v2) if none is provided.
    # This runs locally and is free.
    collection = client.get_or_create_collection(name="nba_knowledge_base")

    documents = [
        "The Boston Celtics won the 2024 NBA Championship.",
        "Jaylen Brown was named the 2024 NBA Finals MVP.",
        "Victor Wembanyama won the 2024 Rookie of the Year award.",
        "Nikola Jokic won the 2023-2024 NBA MVP award.",
        "The NBA In-Season Tournament was won by the Los Angeles Lakers in 2023."
    ]
    
    ids = [f"doc_{i}" for i in range(len(documents))]

    collection.upsert(documents=documents, ids=ids)
    
    print(f"Successfully ingested {len(documents)} documents into ChromaDB.")

if __name__ == "__main__":
    ingest_data()