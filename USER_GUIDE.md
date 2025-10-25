# 🚀 ClinChat HealthAI RAG Application - Complete User Guide

## 📋 Quick Start Checklist

Before you begin, ensure you have:
- ✅ Python 3.11+ installed
- ✅ Git installed  
- ✅ Code editor (VS Code recommended)
- ✅ Internet connection for API keys

---

## 🛠 **STEP 1: Initial Setup**

### 1.1 Clone and Navigate to Project
```bash
cd C:\Users\reddy\Downloads\ClinChat-style-RAG-app
```

### 1.2 Create Virtual Environment  
```bash
# Create virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# You should see (.venv) in your terminal prompt
```

### 1.3 Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### 1.4 Set Up API Keys (IMPORTANT!)
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env file with your actual API keys:
# GROQ_API_KEY=your_groq_key_here
# GOOGLE_API_KEY=your_google_api_key_here
```

**🔑 Get Your API Keys:**
- **Groq API**: Visit https://console.groq.com/keys
- **Google AI**: Visit https://aistudio.google.com/app/apikey

---

## 🎯 **STEP 2: Choose Your Experience**

You have **3 ways** to use the application:

## 🌟 **Option A: Streamlit Dashboard (RECOMMENDED FOR BEGINNERS)**

### Launch the Interactive Dashboard
```bash
streamlit run dashboard.py
```

**What You'll Get:**
- 🔗 **URL**: http://localhost:8501
- 📊 **Real-time Analytics Dashboard**
- 💬 **Interactive Chat Interface** 
- 📈 **Performance Monitoring**
- 🔬 **A/B Testing Results**
- 📋 **Data Quality Reports**

### How to Use the Dashboard:

1. **🏠 Homepage**: Overview of system metrics
2. **💬 Chat Tab**: 
   - Type medical questions
   - Choose AI model (Gemini, Groq, or Fusion)
   - View response confidence scores
   - See processing times

3. **📊 Analytics Tab**:
   - View response quality metrics
   - Monitor model performance
   - Check user satisfaction scores

4. **🧪 A/B Testing Tab**:
   - Compare different AI models
   - View statistical significance
   - Analyze performance differences

---

## 🚀 **Option B: FastAPI Backend (FOR DEVELOPERS)**

### Launch the API Server
```bash
uvicorn src.main:app --reload --port 8000
```

**What You'll Get:**
- 🔗 **API Base**: http://localhost:8000
- 📖 **Interactive Docs**: http://localhost:8000/docs  
- 📚 **Alternative Docs**: http://localhost:8000/redoc
- ❤️ **Health Check**: http://localhost:8000/health

### Key API Endpoints:

#### 💬 **Chat Endpoints**
```bash
# Multi-model AI chat (RECOMMENDED)
POST http://localhost:8000/api/v1/chat/fusion
Content-Type: application/json

{
  "message": "What are the symptoms of diabetes?",
  "use_rag": true,
  "fusion_strategy": "weighted_average"
}

# Simple single-model chat
POST http://localhost:8000/api/v1/chat/simple
Content-Type: application/json

{
  "message": "Explain hypertension treatment options",
  "model": "gemini"
}
```

#### 📄 **Document Management**
```bash
# Upload medical documents
POST http://localhost:8000/api/v1/documents/upload

# Search documents  
POST http://localhost:8000/api/v1/documents/search
Content-Type: application/json

{
  "query": "diabetes treatment guidelines",
  "top_k": 5
}
```

#### 📊 **Monitoring & Analytics**
```bash
# Get performance metrics
GET http://localhost:8000/api/v1/fusion/metrics

# List available AI strategies  
GET http://localhost:8000/api/v1/fusion/strategies
```

---

## 🎨 **Option C: React Frontend (FULL UI EXPERIENCE)**

### Launch the Frontend
```bash
cd frontend
npm install
npm start
```

**What You'll Get:**
- 🔗 **URL**: http://localhost:3000
- 🎨 **Modern React Interface**
- 📱 **Responsive Design**
- 🎯 **Material-UI Components**

---

## 🧪 **STEP 3: Test the Application**

### 3.1 Generate Sample Data (Optional)
```bash
python generate_medical_data.py
```

### 3.2 Run the Test Suite
```bash
pytest tests/ -v
# Should see: ✅ 10 tests passed
```

### 3.3 Try Sample Medical Queries

**Good Test Questions:**
- "What are the early symptoms of Type 2 diabetes?"
- "Explain the difference between systolic and diastolic blood pressure"
- "What medications are commonly prescribed for hypertension?"
- "Describe the stages of chronic kidney disease"
- "What are the risk factors for cardiovascular disease?"

---

## 🎯 **STEP 4: Explore Advanced Features**

### 4.1 A/B Testing Framework
```python
# Run in Python terminal or Jupyter
from src.evaluation.ab_testing import ABTestManager

ab_manager = ABTestManager()
results = ab_manager.run_ab_test(
    queries=["What is diabetes?", "Explain hypertension"],
    models=["gemini", "groq", "fusion"]
)
print(results)
```

### 4.2 Performance Monitoring
```python  
from src.monitoring.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
metrics = monitor.get_current_metrics()
print(f"Average response time: {metrics['avg_response_time']}")
```

### 4.3 Data Science Workflow
```bash
# Run comprehensive data analysis
python data_science_integration.py
```

---

## 📊 **Understanding the Application Components**

### 🤖 **AI Model Fusion**
- **Gemini Pro**: Google's advanced language model
- **Groq**: High-performance inference engine
- **Fusion Strategy**: Combines multiple models for better accuracy

### 🔍 **RAG (Retrieval-Augmented Generation)**
- Searches through medical documents
- Provides context-aware responses  
- Improves accuracy with real medical knowledge

### 📈 **Real-time Analytics**
- Response quality scoring
- Model performance comparison
- User satisfaction tracking
- Data quality validation

---

## 🚨 **Troubleshooting Common Issues**

### ❌ **"ModuleNotFoundError"**
```bash
# Ensure virtual environment is activated
.venv\Scripts\activate
pip install -r requirements.txt
```

### ❌ **"API Key Error"**
```bash
# Check your .env file has correct API keys
echo $env:GROQ_API_KEY  # Should show your key
echo $env:GOOGLE_API_KEY  # Should show your key
```

### ❌ **"Port Already in Use"**
```bash
# Use different ports
uvicorn src.main:app --port 8001  # For API
streamlit run dashboard.py --server.port 8502  # For dashboard
```

### ❌ **"Connection Refused"**
```bash
# Check if services are running
curl http://localhost:8000/health  # Should return {"status": "healthy"}
```

---

## 🎯 **Recommended Usage Workflow**

### **For Medical Professionals:**
1. 🚀 Start with **Streamlit Dashboard** (easiest)
2. 💬 Use **Chat Interface** for medical queries
3. 📊 Monitor **Response Confidence** scores
4. 🔬 Review **Data Quality** reports

### **For Developers:**
1. 🚀 Start with **FastAPI Backend**  
2. 📖 Explore **Interactive API Docs**
3. 🧪 Run **A/B Testing Framework**
4. 📊 Integrate **Performance Monitoring**

### **For Data Scientists:**
1. 🚀 Use **Python Scripts** directly
2. 🧪 Run **Comprehensive Evaluation**
3. 📊 Analyze **Model Performance**
4. 🔬 Conduct **Statistical Analysis**

---

## 📞 **Next Steps & Advanced Usage**

### 🌐 **Production Deployment**
```bash
# Docker deployment
docker build -t healthai-rag .
docker run -p 8000:8000 healthai-rag

# AWS deployment (if configured)
python deploy_production.py
```

### 🔧 **Configuration Customization**
- Edit `src/core/config.py` for app settings
- Modify `dashboard.py` for dashboard customization
- Update `requirements.txt` for additional packages

### 📚 **Documentation**
- 📖 **API Docs**: http://localhost:8000/docs
- 📋 **Project Structure**: See README.md
- 🧪 **Testing Guide**: See pytest.ini

---

## ✨ **Key Features Summary**

| Feature | Description | Access Method |
|---------|-------------|---------------|
| 🤖 **AI Chat** | Multi-model medical assistant | Dashboard/API/Frontend |
| 📄 **Document RAG** | Search medical documents | API endpoints |
| 📊 **Analytics** | Performance monitoring | Dashboard |
| 🧪 **A/B Testing** | Model comparison | Python scripts |
| 🔍 **Evaluation** | Quality assessment | Data science workflow |
| 🌐 **Production** | Scalable deployment | Docker/AWS |

**🎉 You're now ready to use the ClinChat HealthAI RAG application! Start with the Streamlit dashboard for the easiest experience.**