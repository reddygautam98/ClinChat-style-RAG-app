# 🔧 Dependency Installation Guide

## Windows Build Tools Error - Solutions

### **Quick Fix for Local Development**

If you encounter the error:
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Option 1: Install Visual C++ Build Tools (Recommended)**
```powershell
# Download and install Microsoft C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or install Visual Studio Community (includes build tools)
# https://visualstudio.microsoft.com/vs/community/
```

**Option 2: Use Pre-compiled Packages Only**
```powershell
# Install only binary packages (no compilation needed)
pip install --only-binary=all spacy transformers sentence-transformers faiss-cpu
pip install --only-binary=all -r requirements.txt
```

**Option 3: Use Conda (Easiest)**
```powershell
# Install Miniconda: https://docs.conda.io/en/latest/miniconda.html
conda create -n clinchat python=3.12
conda activate clinchat
conda install -c conda-forge spacy transformers sentence-transformers
pip install -r requirements.txt
```

**Option 4: Skip Problematic Packages**
```powershell
# Install everything except packages that need compilation
pip install fastapi uvicorn pydantic redis pandas python-dotenv
pip install pytest pytest-cov httpx matplotlib seaborn
pip install nltk textblob fuzzywuzzy
# Note: Some advanced NLP features may be limited
```

### **For Production/CI-CD (GitHub Actions)**

The GitHub Actions workflow has been updated to:
1. Install system build tools (`build-essential`, `gcc`, `g++`)
2. Try binary-only installation first
3. Fallback to regular installation with build tools
4. Verify critical imports work

### **Alternative Lightweight Setup**

If you want to avoid all compilation issues:

```python
# In your code, add these fallback imports:
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️ SpaCy not available - using basic NLP features")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ SentenceTransformers not available - using basic embeddings")
```

### **Verification Commands**

Test if your installation works:
```powershell
# Test critical imports
python -c "import textblob; print('✅ textblob works')"
python -c "import fuzzywuzzy; print('✅ fuzzywuzzy works')"  
python -c "import spacy; print('✅ spacy works')"
python -c "import sentence_transformers; print('✅ sentence_transformers works')"

# Run basic tests
python -m pytest tests/ -v --tb=short
```

### **Docker Alternative**

If local installation is too problematic, use Docker:
```powershell
# Use the Docker containers which have all dependencies pre-built
docker-compose up healthai-app
```

The Docker containers already have all dependencies compiled and ready to use.