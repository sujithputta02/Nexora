# CUDA Acceleration Setup Guide for Nexora RAG

This guide will help you set up CUDA acceleration to significantly speed up your RAG system's response times.

## 🚀 Performance Improvements

With CUDA acceleration, you can expect:
- **Embeddings**: 10-50x faster (batch processing on GPU)
- **Vector Search**: 3-5x faster (GPU-accelerated FAISS)
- **LLM Inference**: 5-20x faster (depending on model and GPU)
- **Overall Response Time**: 5-15x improvement

## Prerequisites

1. **NVIDIA GPU** with CUDA support (Check: `nvidia-smi`)
2. **CUDA Toolkit** 11.8 or 12.x ([Download](https://developer.nvidia.com/cuda-downloads))
3. **Python 3.9-3.11** (Python 3.12+ may have compatibility issues)

## Step 1: Verify CUDA Installation

```bash
# Check if NVIDIA GPU is detected
nvidia-smi

# Check CUDA version
nvcc --version
```

If `nvidia-smi` or `nvcc` are not found, install CUDA Toolkit first.

## Step 2: Install PyTorch with CUDA Support

The current `requirements.txt` doesn't specify PyTorch version. Install the correct CUDA-enabled version:

### For CUDA 11.8:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### For CUDA 12.1:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Verify PyTorch CUDA:
```bash
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

Expected output:
```
CUDA Available: True
GPU: NVIDIA GeForce RTX 3090 (or your GPU model)
```

## Step 3: Install FAISS-GPU

```bash
# Uninstall CPU version first
pip uninstall faiss-cpu -y

# Install GPU version (for CUDA 11.8)
conda install -c conda-forge faiss-gpu

# OR using pip (may require conda environment)
pip install faiss-gpu
```

**Note**: If you don't have conda, create a conda environment:
```bash
conda create -n nexora python=3.10
conda activate nexora
conda install -c conda-forge faiss-gpu
```

## Step 4: Install Updated Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `torch` (with CUDA support if installed correctly in Step 2)
- `transformers` (for GPU-accelerated models)
- `accelerate` (for optimized GPU inference)
- `faiss-gpu` (GPU-accelerated vector search)

## Step 5: Configure Ollama for GPU (Optional)

If using Ollama, enable GPU acceleration:

```bash
# Set environment variable for Ollama GPU usage
export OLLAMA_NUM_GPU=1

# Or add to .env file
echo "OLLAMA_NUM_GPU=1" >> .env

# Restart Ollama service to pick up GPU
ollama serve
```

Verify Ollama is using GPU:
```bash
ollama run llama3 --verbose
# Should show GPU layers being loaded
```

## Step 6: Choose Your LLM Backend

The CUDA-optimized system supports multiple backends:

### Option A: Ollama with GPU (Easiest)
Already configured if you followed Step 5.

### Option B: Hugging Face Transformers (Good balance)
```bash
# Add to .env
HF_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
BACKEND=transformers
```

Recommended models for different GPU memory sizes:
- **4-6 GB VRAM**: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- **8-12 GB VRAM**: `microsoft/phi-2` or `stabilityai/stablelm-2-1_6b-chat`
- **16+ GB VRAM**: `meta-llama/Llama-2-7b-chat-hf` (requires auth)
- **24+ GB VRAM**: `mistralai/Mistral-7B-Instruct-v0.2`

### Option C: vLLM (Fastest, for production)
```bash
# Install vLLM
pip install vllm

# Add to .env
VLLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
BACKEND=vllm
```

## Step 7: Update Backend Usage (Optional)

To use the new CUDA-optimized backend, you can either:

### A. Modify existing code to use CUDA engine:
```python
# In backend/main_engine.py, add at top:
from backend.llm_engine_cuda import generate_response_cuda, get_gpu_status

# Replace generate_response calls with generate_response_cuda
```

### B. Set environment variable to auto-detect:
```bash
# Add to .env
USE_CUDA=true
BACKEND=auto  # Will auto-select best available backend
```

## Step 8: Rebuild Vector Store with GPU

After installing FAISS-GPU, rebuild your vector store to enable GPU acceleration:

```bash
# Backup existing store
mv data/vector_store data/vector_store.backup

# Rebuild with GPU support
python backend/rebuild_index.py
```

You should see output like:
```
🚀 CUDA Available: True
   GPU Device: NVIDIA GeForce RTX 3090
   GPU Memory: 24.00 GB
   Using device: cuda
🚀 Creating GPU-accelerated FAISS index...
✅ GPU-accelerated index created successfully
```

## Step 9: Test GPU Performance

```bash
python test_cuda_performance.py
```

Or test manually:
```python
from backend.vector_store import get_embeddings, load_vector_store
from backend.llm_engine_cuda import get_gpu_status, initialize_backend

# Check GPU status
print(get_gpu_status())

# Test embeddings
embeddings = get_embeddings()
test_texts = ["ISRO Chandrayaan-3 mission"] * 100
import time
start = time.time()
embeddings.embed_documents(test_texts)
print(f"Embedding time: {time.time() - start:.2f}s")

# Test vector search
vector_store = load_vector_store()
results = vector_store.similarity_search("Chandrayaan-3", k=5)
print(f"Found {len(results)} results")
```

## Step 10: Start the Application

```bash
python app/app.py
```

Check the startup logs for GPU confirmation:
```
🚀 CUDA Available: True
   GPU Device: NVIDIA GeForce RTX 3090
   GPU Memory: 24.00 GB
   Using device: cuda
✅ Embeddings model loaded successfully on CUDA
⚡ Index Load Latency (GPU): 45.23 ms
🔧 Initializing backend: transformers
✅ Transformers backend initialized on CUDA
```

## Troubleshooting

### Issue: "CUDA not available" despite having GPU

**Solution**:
```bash
# Reinstall PyTorch with correct CUDA version
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: "FAISS-GPU not found" or import errors

**Solution**:
```bash
# Use conda for reliable FAISS-GPU installation
conda install -c conda-forge faiss-gpu
```

### Issue: Out of memory errors

**Solutions**:
1. Reduce batch size in embeddings:
   ```python
   # In vector_store.py
   encode_kwargs={'batch_size': 64}  # Reduce from 128
   ```

2. Use smaller model:
   ```bash
   # In .env
   HF_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
   ```

3. Enable model quantization:
   ```python
   # In llm_engine_cuda.py
   torch_dtype=torch.int8  # Instead of float16
   ```

### Issue: Ollama not using GPU

**Solution**:
```bash
# Check Ollama GPU status
ollama ps

# Set GPU layers explicitly
export OLLAMA_NUM_GPU=1
export OLLAMA_GPU_LAYERS=35  # Adjust based on your model

# Restart Ollama
killall ollama
ollama serve
```

### Issue: Slow performance despite GPU

**Checklist**:
1. ✅ PyTorch CUDA is available: `python -c "import torch; print(torch.cuda.is_available())"`
2. ✅ FAISS index is on GPU: Check logs for "GPU-accelerated index"
3. ✅ Model is on GPU: Check logs for "initialized on CUDA"
4. ✅ Correct GPU is selected: `export CUDA_VISIBLE_DEVICES=0`

## Performance Benchmarking

Test your setup with different configurations:

```bash
# CPU baseline (for comparison)
USE_CUDA=false python benchmark.py

# GPU with different backends
BACKEND=ollama python benchmark.py
BACKEND=transformers python benchmark.py
BACKEND=vllm python benchmark.py
```

## Configuration Reference

All CUDA-related settings in `.env`:

```bash
# GPU Configuration
USE_CUDA=true
CUDA_VISIBLE_DEVICES=0  # Which GPU to use (0, 1, 2, etc.)

# Backend Selection
BACKEND=auto  # auto, transformers, vllm, ollama, fallback

# Ollama GPU
OLLAMA_NUM_GPU=1
OLLAMA_GPU_LAYERS=35

# Hugging Face Model (for transformers/vllm backend)
HF_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
VLLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0

# Performance Tuning
EMBEDDING_BATCH_SIZE=128
MAX_MODEL_LEN=2048
GPU_MEMORY_UTILIZATION=0.8
```

## Expected Performance Metrics

### Before CUDA (CPU):
- Embedding 100 docs: ~5-10 seconds
- Vector search: ~100-200 ms
- LLM response: ~10-30 seconds
- Total query time: ~15-40 seconds

### After CUDA (GPU):
- Embedding 100 docs: ~0.5-1 second (10x faster)
- Vector search: ~20-50 ms (4x faster)
- LLM response: ~1-3 seconds (10x faster)
- Total query time: ~2-5 seconds (10x faster)

## Next Steps

1. **Monitor GPU usage**: `watch -n 1 nvidia-smi`
2. **Profile performance**: Use the analytics dashboard
3. **Optimize batch sizes**: Tune based on your GPU memory
4. **Consider model quantization**: For even faster inference

## Additional Resources

- [PyTorch CUDA Installation](https://pytorch.org/get-started/locally/)
- [FAISS GPU Guide](https://github.com/facebookresearch/faiss/wiki/Faiss-on-the-GPU)
- [vLLM Documentation](https://docs.vllm.ai/)
- [Ollama GPU Configuration](https://github.com/ollama/ollama/blob/main/docs/gpu.md)
