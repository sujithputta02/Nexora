# main.py

from backend.ingestion import load_documents, split_documents

if __name__ == "__main__":
    folder_path = "data/isro_docs"

    docs = load_documents(folder_path)
    print(f"Loaded {len(docs)} documents")

    chunks = split_documents(docs)
    print(f"Generated {len(chunks)} chunks")

    print("\nSample Chunk:\n")
    print(chunks[0])
