# HealthAI RAG Application

An advanced clinical chat application using Retrieval-Augmented Generation (RAG) for medical knowledge assistance. Features AI model fusion, comprehensive evaluation framework, A/B testing, and performance monitoring.

# Dashboard 
<img width="2537" height="1240" alt="Screenshot 2025-10-23 224431" src="https://github.com/user-attachments/assets/f3490e95-5a03-4a1b-9cc8-fb3fc83bcdfa" />

<img width="1536" height="1024" alt="ChatGPT Image Oct 27, 2025, 07_43_41 AM" src="https://github.com/user-attachments/assets/a7f1f85d-8efd-408c-8022-f1f1322497b3" />

## 🌟 Features

- **Multi-Model AI Fusion**: Combines multiple AI models for enhanced responses
- **RAG System**: Advanced retrieval-augmented generation for medical knowledge
- **A/B Testing Framework**: Compare different AI models and strategies
- **Performance Monitoring**: Real-time metrics and analytics dashboard
- **Data Quality Analysis**: Comprehensive data validation and quality reporting
- **Evaluation Framework**: Automated testing and performance benchmarking
- **Streamlit Dashboard**: Interactive web interface for monitoring and analysis
- **FastAPI Backend**: High-performance REST API with automatic documentation

## 🛠 Prerequisites

- Python 3.12+ (3.12.1 recommended)
- Docker Desktop (optional)
- VS Code with Python extensions
- Git
- AWS CLI (for deployment)

## Setup

1. **Clone the repository:**
```bash
git clone https://github.com/reddygautam98/ClinChat-style-RAG-app.git
cd ClinChat-style-RAG-app
```

2. **Create and activate virtual environment:**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
# Create .env file with your API keys
echo "GROQ_API_KEY=your_groq_key_here" > .env
echo "GOOGLE_API_KEY=your_google_key_here" >> .env
echo "OPENAI_API_KEY=your_openai_key_here" >> .env
```

5. **Generate sample medical data (optional):**
```bash
python generate_medical_data.py
```

6. **Run the FastAPI application:**
```bash
uvicorn src.main:app --reload --port 8000
```

7. **Or run the Streamlit dashboard:**
```bash
streamlit run dashboard.py
```

## 📁 Project Structure

```
HealthAI-RAG/
├── src/                          # Source code
│   ├── main.py                  # FastAPI application entry point
│   ├── api/                     # API routes and endpoints
│   │   ├── app.py              # Main API application
│   │   ├── chat.py             # Chat endpoints
│   │   ├── documents.py        # Document management
│   │   └── routes.py           # Route definitions
│   ├── core/                    # Core application logic
│   │   └── config.py           # Configuration settings
│   ├── evaluation/              # Evaluation and testing framework
│   │   ├── rag_evaluator.py    # RAG system evaluation
│   │   ├── ab_testing.py       # A/B testing framework
│   │   └── test_dataset_generator.py # Test data generation
│   ├── services/                # Business logic services
│   │   └── fusion_ai.py        # AI model fusion service
│   ├── vectorstore/             # Vector database management
│   │   └── faiss_store.py      # FAISS vector store implementation
│   ├── ingestion/               # Document processing
│   │   └── pdf_parser.py       # PDF document parser
│   ├── embeddings/              # Text embedding services
│   │   └── openai_embed.py     # OpenAI embedding integration
│   ├── monitoring/              # Performance monitoring
│   │   └── performance_monitor.py # Metrics and monitoring
│   └── models/                  # Pydantic data models
│       └── fusion_models.py    # AI model definitions
├── tests/                       # Comprehensive test suite
│   └── test_main.py            # API endpoint tests
├── data/                        # Data files and datasets
│   ├── clinical_data_5000.csv  # Sample medical data
│   ├── vectorstore/            # FAISS index files
│   └── ab_test_results/        # A/B testing results
├── dashboard.py                 # Streamlit dashboard application
├── data_science_integration.py  # Data science workflow controller
├── generate_medical_data.py     # Medical data generator
├── requirements.txt             # Python dependencies
├── pytest.ini                  # Test configuration
├── Dockerfile                  # Docker configuration
└── README.md                   # This file
```

## 🚀 Available Applications

### FastAPI Backend (Port 8000)
- **Main Application**: http://127.0.0.1:8000/
- **Interactive API Docs**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health

### Streamlit Dashboard (Port 8501)
- **Analytics Dashboard**: http://127.0.0.1:8501/
- **Performance Metrics**: Real-time monitoring
- **A/B Test Results**: Comparative analysis
- **Data Quality Reports**: Comprehensive insights

## 🔧 Key Endpoints

### Chat API
- **POST** `/api/v1/chat/fusion` - Multi-model AI chat
- **POST** `/api/v1/chat/simple` - Single model chat
- **GET** `/api/v1/chat/health` - Chat service health

### Document Management
- **POST** `/api/v1/documents/upload` - Upload medical documents
- **GET** `/api/v1/documents/` - List documents
- **POST** `/api/v1/documents/search` - Search documents

### Monitoring & Analytics
- **GET** `/api/v1/fusion/metrics` - Performance metrics
- **GET** `/api/v1/fusion/strategies` - Available AI strategies

## 🧪 Testing & Evaluation

### Run Complete Test Suite
```bash
pytest tests/ -v
# All 10 tests should pass ✅
```

### Run Comprehensive Evaluation
```bash
python data_science_integration.py
```

### Generate Test Data
```bash
python generate_medical_data.py
```

### A/B Testing Framework
```bash
# Import and use the A/B testing system
from src.evaluation.ab_testing import ABTestManager
ab_manager = ABTestManager()
```

### Performance Monitoring
The application includes real-time monitoring of:
- Response times
- Confidence scores  
- User satisfaction
- Model performance
- Data quality metrics

## 🐳 Docker Deployment

### Standard Deployment
```bash
docker build -t healthai-rag .
docker run -p 8000:8000 healthai-rag
```

### Optimized Production Build
```bash
docker build -f Dockerfile.optimized -t healthai-rag-prod .
docker run -p 8000:8000 healthai-rag-prod
```

### Fast Development Build
```bash
docker build -f Dockerfile.fast -t healthai-rag-dev .
docker run -p 8000:8000 healthai-rag-dev
```

## ☁️ AWS Deployment

The application is ready for AWS ECS deployment:

1. **Set up AWS OIDC** (run once):
```powershell
./setup-aws-oidc.ps1
```

2. **Deploy to ECS**:
```bash
# Push happens automatically via GitHub Actions
# on push to main branch
git push origin main
```

3. **Monitor deployment**: Check GitHub Actions for deployment status

## 🏗️ Architecture

### AI Model Fusion
- **Multiple Models**: Groq, Google Gemini, OpenAI integration
- **Fusion Strategies**: Voting, weighted average, confidence-based
- **Dynamic Selection**: Context-aware model selection

### Data Science Framework
- **Evaluation Metrics**: Precision@K, Recall@K, NDCG, MRR
- **A/B Testing**: Statistical significance testing
- **Performance Monitoring**: Real-time metrics collection
- **Data Quality**: Automated analysis and reporting

### Scalability Features
- **Vector Database**: FAISS for efficient similarity search
- **Async Processing**: High-performance concurrent operations  
- **Caching**: Optimized response caching
- **Monitoring**: Prometheus-compatible metrics

## 📊 Current Status

- ✅ **All Tests Passing**: 10/10 test suite success
- ✅ **Code Quality**: Lint errors resolved, clean codebase
- ✅ **Dependencies**: All 200+ packages installed and working
- ✅ **Documentation**: Comprehensive API documentation
- ✅ **Deployment Ready**: AWS ECS configuration complete
- ✅ **Monitoring**: Performance tracking operational

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/`)
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♀️ Support

For support and questions:
- Create an issue on GitHub
- Check the documentation at `/docs`
- Review API documentation at `/docs` endpoint

## 🔄 Version History

- **v1.0.0** - Initial HealthAI RAG release with full feature set
- **v0.9.0** - Added A/B testing and evaluation framework  
- **v0.8.0** - Implemented multi-model AI fusion
- **v0.7.0** - Added Streamlit dashboard and monitoring

---

**Built with ❤️ for advancing healthcare through AI**
