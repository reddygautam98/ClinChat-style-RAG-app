# ClinChat RAG Application

A clinical chat application using Retrieval-Augmented Generation (RAG) for medical knowledge assistance.

## Prerequisites

- Python 3.11+ (or 3.10)
- Docker Desktop
- VS Code with required extensions
- Git
- AWS CLI (optional)

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd clinchat-rag
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Run the application:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
clinchat-rag/
├── src/                    # Source code
│   ├── main.py            # FastAPI application entry point
│   ├── api/               # API routes
│   ├── core/              # Core application logic
│   ├── models/            # Pydantic models
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── tests/                 # Test files
├── docs/                  # Documentation
├── data/                  # Data files and vector stores
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── Dockerfile            # Docker configuration
└── README.md             # This file
```

## API Documentation

Once running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Testing

Run tests with:
```bash
pytest tests/
```

## Docker

Build and run with Docker:
```bash
docker build -t clinchat-rag .
docker run -p 8000:8000 clinchat-rag
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request