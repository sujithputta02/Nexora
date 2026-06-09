import os
import torch
import platform
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

# Detect acceleration support
_USE_CUDA = torch.cuda.is_available()
_USE_MPS = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
_IS_MAC = platform.system() == 'Darwin'

def get_embeddings():
    """
    Initializes the HuggingFace embeddings model with hardware acceleration.
    Supports: CUDA (NVIDIA), MPS (Apple Silicon), optimized CPU
    Checks for local cache first to support offline mode.
    """
    global _CACHED_EMBEDDINGS, _USE_CUDA, _USE_MPS
    
    if _CACHED_EMBEDDINGS is None:
        print("Loading embeddings model... (This happens once)")
        
        # Determine best device
        if _USE_CUDA:
            device = 'cuda'
            print(f"🚀 CUDA Available: True")
            print(f"   GPU Device: {torch.cuda.get_device_name(0)}")
            print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        elif _USE_MPS:
            device = 'mps'
            print(f"🍎 Apple Silicon (MPS) Available: True")
            print(f"   Using Metal Performance Shaders for acceleration")
        else:
            device = 'cpu'
            if _IS_MAC:
                print(f"💻 Running on Mac with optimized CPU")
            else:
                print(f"💻 Using CPU")
        
        print(f"   Using device: {device.upper()}")
        
        # Check if running offline and model exists locally
        default_cache_path = os.path.expanduser("~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf")
        
        # Allow override via environment variable
        local_model_path = os.getenv("SENTENCE_TRANSFORMERS_HOME", default_cache_path)

        # Determine batch size based on device
        if _USE_CUDA:
            batch_size = 128
        elif _USE_MPS:
            batch_size = 64  # MPS is efficient but not as fast as CUDA
        else:
            batch_size = 32

        try:
            if os.path.exists(local_model_path):
                print(f"Loading embedding model from local cache: {local_model_path}")
                _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(
                    model_name=local_model_path,
                    model_kwargs={
                        'device': device,
                        'trust_remote_code': True
                    },
                    encode_kwargs={
                        'batch_size': batch_size,
                        'normalize_embeddings': True
                    }
                )
            else:
                print(f"Local model not found at {local_model_path}, attempting download/load from Hub...")
                _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(
                    model_name=MODEL_NAME,
                    model_kwargs={
                        'device': device,
                        'trust_remote_code': True
                    },
                    encode_kwargs={
                        'batch_size': batch_size,
                        'normalize_embeddings': True
                    }
                )
            print(f"✅ Embeddings model loaded successfully on {device.upper()}")
        except Exception as e:
            print(f"Error loading embeddings model on {device}: {e}")
            if device != 'cpu':
                print("Falling back to CPU mode...")
                _USE_CUDA = False
                _USE_MPS = False
                _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(
                    model_name=MODEL_NAME,
                    model_kwargs={'device': 'cpu'}
                )
            else:
                raise e
            
    return _CACHED_EMBEDDINGS

def create_vector_store(documents):
    """
    Creates a FAISS vector store from the provided documents and saves it locally.
    Uses GPU-accelerated FAISS index if CUDA is available.
    On Mac, uses optimized CPU FAISS (MPS not supported by FAISS yet).
    """
    import numpy as np
    from langchain_community.docstore.in_memory import InMemoryDocstore
    
    embeddings = get_embeddings()
    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]
    
    print("Generating embeddings for FAISS index...")
    print(f"🔧 Processing {len(texts)} documents...")
    
    # Generate embeddings in batches for efficiency
    text_embeddings = embeddings.embed_documents(texts)
    
    d = len(text_embeddings[0])
    
    # Create GPU-accelerated index if CUDA is available (FAISS doesn't support MPS)
    if _USE_CUDA:
        print("🚀 Creating GPU-accelerated FAISS index...")
        try:
            # Create GPU resources
            res = faiss.StandardGpuResources()
            
            # Create a flat index on CPU first
            cpu_index = faiss.IndexFlatL2(d)
            
            # Move to GPU
            gpu_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
            
            print("✅ GPU-accelerated index created successfully")
            index = gpu_index
        except Exception as e:
            print(f"⚠️  GPU index creation failed: {e}")
            print("   Falling back to CPU index...")
            index = faiss.index_factory(d, "Flat")
    else:
        if _USE_MPS or _IS_MAC:
            print("Using optimized CPU Flat Index (FAISS doesn't support MPS yet)...")
        else:
            print("Using CPU Flat Index...")
        index = faiss.index_factory(d, "Flat")
    
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
    print(f"✅ Vector store saved to {VECTOR_STORE_PATH}")
    return vector_store

import time

def load_vector_store():
    """
    Loads the FAISS vector store from the local path with GPU acceleration if available.
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
        _CACHED_VECTOR_STORE = FAISS.load_local(
            VECTOR_STORE_PATH, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # Try to move index to GPU if CUDA available (not MPS - FAISS doesn't support it)
        if _USE_CUDA and hasattr(_CACHED_VECTOR_STORE, 'index'):
            try:
                print("🚀 Moving FAISS index to GPU for faster search...")
                global _FAISS_GPU_RES
                if '_FAISS_GPU_RES' not in globals() or _FAISS_GPU_RES is None:
                    _FAISS_GPU_RES = faiss.StandardGpuResources()
                gpu_index = faiss.index_cpu_to_gpu(_FAISS_GPU_RES, 0, _CACHED_VECTOR_STORE.index)
                _CACHED_VECTOR_STORE.index = gpu_index
                print("✅ Index successfully moved to GPU")
            except Exception as e:
                print(f"⚠️  Could not move index to GPU: {e}")
                print("   Continuing with CPU index...")
        
        load_latency = (time.time() - start_time) * 1000
        
        if _USE_CUDA:
            device_str = "GPU (CUDA)"
        elif _USE_MPS:
            device_str = "CPU (with MPS embeddings)"
        else:
            device_str = "CPU"
        
        print(f"⚡ Index Load Latency ({device_str}): {load_latency:.2f} ms")
        
        return _CACHED_VECTOR_STORE
    else:
        return None
