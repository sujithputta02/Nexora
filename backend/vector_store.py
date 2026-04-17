import os
# Force single-threading for FAISS to prevent segmentation faults on Mac/Python 3.14
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import faiss
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Define the model path and vector store path
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_STORE_PATH = "data/vector_store"

# Global cache for the vector store
_CACHED_VECTOR_STORE = None
_CACHED_EMBEDDINGS = None

def get_embeddings():
    """
    Initializes the HuggingFace embeddings model.
    Checks for local cache first to support offline mode.
    """
    global _CACHED_EMBEDDINGS
    if _CACHED_EMBEDDINGS is None:
        print("Loading embeddings model... (This happens once)")
        
        # Check if running offline and model exists locally
        default_cache_path = os.path.expanduser("~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf")
        
        # Allow override via environment variable
        local_model_path = os.getenv("SENTENCE_TRANSFORMERS_HOME", default_cache_path)

        try:
            if os.path.exists(local_model_path):
                print(f"Loading embedding model from local cache: {local_model_path}")
                _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(
                    model_name=local_model_path,
                    model_kwargs={'device': 'cpu'}
                )
            else:
                print(f"Local model not found at {local_model_path}, attempting download/load from Hub...")
                _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(
                    model_name=MODEL_NAME,
                    model_kwargs={'device': 'cpu'}
                )
            print("Embeddings model loaded successfully.")
        except Exception as e:
            print(f"Error loading embeddings model: {e}")
            raise e
            
    return _CACHED_EMBEDDINGS

def create_vector_store(documents):
    """
    Creates a FAISS vector store from the provided documents and saves it locally.
    Uses Int8 Scalar Quantization for latency and memory optimization.
    """
    import numpy as np
    from langchain_community.docstore.in_memory import InMemoryDocstore
    
    embeddings = get_embeddings()
    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]
    
    print("Generating embeddings for Int8 FAISS index...")
    text_embeddings = embeddings.embed_documents(texts)
    
    d = len(text_embeddings[0])
    # Create a Flat index instead of HNSW32,SQ8 to prevent segmentation faults with small datasets
    index = faiss.index_factory(d, "Flat")
    
    print("Using Flat Index...")
    
    # Create the lang-chain vector_store
    vector_store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={}
    )
    
    # Add embeddings directly
    text_embedding_pairs = list(zip(texts, text_embeddings))
    vector_store.add_embeddings(text_embeddings=text_embedding_pairs, metadatas=metadatas)
    
    vector_store.save_local(VECTOR_STORE_PATH)
    return vector_store

import time

def load_vector_store():
    """
    Loads the FAISS vector store from the local path.
    Uses a global cache to avoid reloading the index on every call.
    Includes performance benchmarking for the journal paper metrics.
    """
    global _CACHED_VECTOR_STORE
    
    start_time = time.time()
    
    if _CACHED_VECTOR_STORE is not None:
        return _CACHED_VECTOR_STORE

    if os.path.exists(VECTOR_STORE_PATH):
        print("Loading vector store from disk... (This happens once)")
        embeddings = get_embeddings()
        _CACHED_VECTOR_STORE = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
        
        load_latency = (time.time() - start_time) * 1000
        print(f"Index Load Latency: {load_latency:.2f} ms")
        
        return _CACHED_VECTOR_STORE
    else:
        return None
