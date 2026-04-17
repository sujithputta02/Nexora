# Secure ISRO RAG System

## Overview
This is an offline, secure, graph-augmented Retrieval-Augmented Generation (RAG) system designed for ISRO domain documents. It combines Vector Search (FAISS) with Knowledge Graph (Neo4j) validation to reduce hallucinations and enforce Role-Based Access Control (RBAC).

## Features
- **Offline Capability**: Runs locally without external API calls.
- **Hybrid Validation**: Validates vector retrieval against a Knowledge Graph.
- **RBAC**: Restricts access based on user roles (Scientist, Engineer, Public).
- **Audit Logging**: Logs all queries and validation results to SQLite.

## Project Structure
```
rag_offline/
├── app/
│   ├── app.py                 # FastAPI Backend
│   └── templates/
│       └── index.html         # Frontend Interface
├── backend/
│   ├── ingestion.py           # Content Processing
│   ├── vector_store.py        # FAISS Integration
│   ├── graph_store.py         # Neo4j Integration
│   ├── retriever.py           # Search Logic
│   ├── validator.py           # Hybrid Validation Engine
│   ├── rbac.py                # Security Logic
│   ├── logger.py              # Audit Logging
│   ├── llm_engine.py          # Constrained Generation
│   ├── main_engine.py         # Orchestrator
│   └── populate_db.py         # Data Loading Script
├── data/
│   └── isro_docs/             # Place PDFs here
├── logs/                      # Audit logs
└── requirements.txt
```

## Setup & Run
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Setup Neo4j**:
    -   Download and install Neo4j Desktop.
    -   Create a Local DBMS.
    -   Set password to `password` (or update `.env`).
3.  **Add Data**:
    -   Place ISRO PDFs in `data/isro_docs/`.
4.  **Populate Database**:
    ```bash
    python -m backend.populate_db
    ```
5.  **Run Application**:
    ```bash
    python -m app.app
    ```
    Access the UI at `http://127.0.0.1:8000`.

## Contact
For issues, please contact the maintainer.
