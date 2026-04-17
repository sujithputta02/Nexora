import os
import shutil
from backend.ingestion import load_documents, split_documents
from backend.vector_store import create_vector_store
from backend.graph_store import GraphStore

def rebuild():
    print("--- Starting Full Index Rebuild (Sovereign Hybrid RAG) ---")
    
    # 1. Clear existing Graph Data (Optional but recommended for full rebuild)
    # Note: Using execute_query to wipe the DB if accessible
    try:
        graph = GraphStore()
        print("Clearing existing Knowledge Graph...")
        with graph._get_session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        graph.setup_schema()
    except Exception as e:
        print(f"Warning: Could not clear graph: {e}")
        graph = None

    # 2. Clear existing Vector Store
    if os.path.exists("data/vector_store"):
        print("Clearing existing Vector Store...")
        shutil.rmtree("data/vector_store")

    # 3. Load Documents from Archive (both small and large)
    print("Loading documents from data/isro_docs...")
    docs = load_documents("data/isro_docs")
    
    print("Loading documents from data/isro_docs_large...")
    docs_large = load_documents("data/isro_docs_large")
    docs.extend(docs_large)
    
    if not docs:
        print("No documents found. Checking data/archive...")
        docs = load_documents("data/archive")

    # 4. Split and Populate Graph (Happens inside split_documents now)
    print("Splitting documents and populating Knowledge Graph...")
    chunks = split_documents(docs)
    
    # 5. Create Vector Store
    print(f"Creating Vector Store with {len(chunks)} chunks...")
    create_vector_store(chunks)
    
    if graph:
        count = graph.count_nodes()
        print(f"Total Nodes: {count}")
        graph.close()

    print("\n--- Rebuild Complete! ---")
    print("Vector Store: data/vector_store")
    print("Knowledge Graph: Check Neo4j Bloom or Browser")

if __name__ == "__main__":
    rebuild()
