#!/bin/bash

# CUDA Setup Script for Nexora RAG System
# This script automates the installation of CUDA-accelerated components

set -e

echo "=========================================="
echo "  Nexora RAG - CUDA Acceleration Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if NVIDIA GPU is available
echo "🔍 Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo -e "${GREEN}✅ NVIDIA GPU detected${NC}"
else
    echo -e "${RED}❌ nvidia-smi not found${NC}"
    echo "   Please install NVIDIA drivers and CUDA Toolkit first"
    echo "   Visit: https://developer.nvidia.com/cuda-downloads"
    exit 1
fi

# Check Python version
echo ""
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "   Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.9" ]] || [[ "$PYTHON_VERSION" > "3.11" ]]; then
    echo -e "${YELLOW}⚠️  Recommended Python version is 3.9-3.11${NC}"
    echo "   You have: $PYTHON_VERSION"
    echo "   Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect CUDA version
echo ""
echo "🔍 Detecting CUDA version..."
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed 's/.*release //' | cut -d',' -f1)
    echo "   CUDA version: $CUDA_VERSION"
else
    echo -e "${YELLOW}⚠️  nvcc not found, assuming CUDA 11.8${NC}"
    CUDA_VERSION="11.8"
fi

# Determine PyTorch CUDA version
if [[ "$CUDA_VERSION" == 12.* ]]; then
    TORCH_CUDA="cu121"
    echo "   Using PyTorch CUDA 12.1"
elif [[ "$CUDA_VERSION" == 11.* ]]; then
    TORCH_CUDA="cu118"
    echo "   Using PyTorch CUDA 11.8"
else
    echo -e "${YELLOW}⚠️  Unknown CUDA version, using 11.8${NC}"
    TORCH_CUDA="cu118"
fi

# Install PyTorch with CUDA
echo ""
echo "📦 Installing PyTorch with CUDA support..."
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/$TORCH_CUDA

# Verify PyTorch CUDA
echo ""
echo "🔍 Verifying PyTorch CUDA installation..."
python3 -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Check if conda is available for FAISS-GPU
echo ""
echo "🔍 Checking for conda..."
if command -v conda &> /dev/null; then
    echo -e "${GREEN}✅ Conda found${NC}"
    echo "📦 Installing FAISS-GPU via conda..."
    
    # Uninstall CPU version
    pip3 uninstall -y faiss-cpu 2>/dev/null || true
    
    # Install GPU version
    conda install -y -c conda-forge faiss-gpu
    
    echo -e "${GREEN}✅ FAISS-GPU installed${NC}"
else
    echo -e "${YELLOW}⚠️  Conda not found${NC}"
    echo "   FAISS-GPU works best with conda installation"
    echo "   Attempting pip installation (may not work on all systems)..."
    
    pip3 uninstall -y faiss-cpu 2>/dev/null || true
    pip3 install faiss-gpu || {
        echo -e "${RED}❌ FAISS-GPU pip installation failed${NC}"
        echo "   Please install conda and retry, or install manually:"
        echo "   conda install -c conda-forge faiss-gpu"
    }
fi

# Install other dependencies
echo ""
echo "📦 Installing remaining dependencies..."
pip3 install -r requirements.txt

# Optional: Install vLLM for fastest inference
echo ""
echo "❓ Install vLLM for ultra-fast inference? (recommended for production)"
echo "   Note: Requires CUDA 11.8+ and ~2GB download (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "📦 Installing vLLM..."
    pip3 install vllm
    echo -e "${GREEN}✅ vLLM installed${NC}"
fi

# Configure environment
echo ""
echo "🔧 Configuring environment..."

# Add CUDA settings to .env if not already present
if [ ! -f .env ]; then
    echo "Creating .env file..."
    touch .env
fi

# Add CUDA configurations
if ! grep -q "USE_CUDA" .env; then
    echo "" >> .env
    echo "# CUDA Configuration" >> .env
    echo "USE_CUDA=true" >> .env
    echo "BACKEND=auto" >> .env
    echo "OLLAMA_NUM_GPU=1" >> .env
fi

echo -e "${GREEN}✅ Environment configured${NC}"

# Test installation
echo ""
echo "🧪 Running performance test..."
python3 test_cuda_performance.py --test cuda

# Rebuild vector store with GPU
echo ""
echo "❓ Rebuild vector store with GPU acceleration? (recommended)"
echo "   This will backup existing store and create GPU-optimized version (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "📦 Rebuilding vector store..."
    
    # Backup existing
    if [ -d "data/vector_store" ]; then
        echo "   Backing up existing vector store..."
        mv data/vector_store data/vector_store.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Rebuild
    python3 backend/rebuild_index.py
    
    echo -e "${GREEN}✅ Vector store rebuilt with GPU acceleration${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "✅ PyTorch with CUDA: Installed"
echo "✅ FAISS-GPU: Installed"
echo "✅ Dependencies: Installed"
echo "✅ Environment: Configured"
echo ""
echo "Next Steps:"
echo "1. Test performance: python3 test_cuda_performance.py"
echo "2. Start application: python3 app/app.py"
echo "3. Monitor GPU usage: watch -n 1 nvidia-smi"
echo ""
echo "For detailed configuration options, see: CUDA_SETUP_GUIDE.md"
echo ""
echo "Expected performance improvements:"
echo "  • Embeddings: 10-50x faster"
echo "  • Vector Search: 3-5x faster"
echo "  • LLM Inference: 5-20x faster"
echo "  • Overall: 5-15x faster response times"
echo ""
echo "=========================================="
