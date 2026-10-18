# HealthAI RAG — Clinical Information Retrieval Prototype

A learning and portfolio project exploring retrieval-augmented generation (RAG) for searching a collection of healthcare information documents. The repository contains a Python/FastAPI backend, retrieval and embedding modules, a React/Material UI frontend, and development/evaluation utilities.

> **Safety and status:** This is an experimental software prototype, not a medical device and not validated for clinical decision-making. No HIPAA, security, or production-readiness certification is claimed. Do not submit real patient information or other sensitive data. Outputs can be incomplete or incorrect and must not replace professional medical advice.

## Screenshots

### Dashboard

<img width="1270" alt="HealthAI dashboard screenshot" src="https://github.com/user-attachments/assets/f3490e95-5a03-4a1b-9cc8-fb3fc83bcdfa" />

### Architecture concept

<img width="960" alt="HealthAI architecture diagram" src="https://github.com/user-attachments/assets/21b83e29-e274-451f-bea1-fb44a0a37d35" />

## What the repository contains

- **FastAPI application** in `src/main.py`, including a health endpoint and API router.
- **Chat and document routes** registered through `src/api/routes.py`.
- **RAG building blocks** in `src/rag/` for retrieving relevant documents and preparing contextual answers.
- **Embedding providers** including Sentence Transformers and Google Gemini in `src/embeddings/`.
- **Vector-search code** in `src/vectorstore/`, including a FAISS store module.
- **Model-provider integration** in `src/services/fusion_ai.py` for Gemini and Groq, with configurable response-fusion logic.
- **PDF ingestion** in `src/ingestion/`.
- **React + Material UI frontend** in `frontend/`.
- **Evaluation and monitoring modules** in `src/evaluation/` and `src/monitoring/`. These are code components to review and test; their presence is not evidence of measured performance or passing evaluations.
- **Docker and Compose files** for exploring container-based development.

## Technology stack

Python, FastAPI, Pydantic, React, TypeScript, Material UI, FAISS, Sentence Transformers, Google Gemini, Groq, Redis (optional configuration), Docker, pytest.

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/reddygautam98/ClinChat-style-RAG-app.git
cd ClinChat-style-RAG-app
```

### 2. Create a Python environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and add your own provider keys if required:

```dotenv
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

Use a local-only secret file, do not commit real API keys, and rotate any key that has been accidentally exposed. Check `src/core/config.py` for the settings consumed by the current backend.

### 4. Run the API

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- API root: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Interactive API docs: http://127.0.0.1:8000/docs

The API documentation shows the routes registered by the backend currently running in your environment.

### 5. Run the frontend (optional)

```bash
cd frontend
npm install
npm start
```

The frontend and backend route/configuration assumptions should be checked together before expecting end-to-end chat to work. See the known limitations below.

## Known limitations and verification status

- Treat this as a development/portfolio prototype. The repository includes some placeholder code and planned or partially implemented modules.
- Review API route compatibility between the frontend and backend before claiming a working end-to-end integration.
- Run the test suite in a clean environment before reporting a coverage percentage or passing-test status. This README does not claim a measured coverage level, benchmark result, or successful production deployment.
- Validate retrieval quality and answer grounding on a clearly defined test dataset before making accuracy claims.
- Review authentication, logging, data retention, dependency security and infrastructure settings before any use with sensitive data.
- Do not describe the software as HIPAA-compliant or clinically validated without a formal, independently substantiated basis.

## Project structure

```text
src/
  api/          FastAPI routes for chat and documents
  core/         Application configuration
  embeddings/   Text embedding providers
  evaluation/   RAG evaluation utilities
  ingestion/    Document/PDF processing
  monitoring/   Monitoring-related modules
  rag/          Retrieval and answer-generation logic
  services/     Model-provider and fusion logic
  vectorstore/  Vector-search implementation
frontend/       React/TypeScript UI
data/           Local sample data and vector-store assets
tests/          Test suite, where available
Dockerfile      Container build definition
docker-compose.dev.yml  Development services
requirements.txt        Python dependencies
.env.example            Example environment configuration
```

## Next steps for a portfolio review

1. Demonstrate the API startup and health endpoint in a clean environment.
2. Verify the frontend-to-backend request paths.
3. Run and document the tests that actually pass.
4. Add a small reproducible RAG evaluation with the dataset, scoring approach and results.
5. Document the implemented behavior separately from future ideas.

## Contributing

Issues and pull requests are welcome. Please include reproduction steps for defects and tests for behavior changes where practical.

## License

See the repository's `LICENSE` file for the applicable license.
