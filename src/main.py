from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
import os
import uvicorn
from src.core.config import settings
from src.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # Shutdown
    print("Shutting down HealthAI RAG application")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="HealthAI chat application with RAG capabilities",
    lifespan=lifespan
)

# Add CORS middleware with security-first configuration
allowed_origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8000",  # FastAPI dev server  
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000"
]

# Add production origins from environment if available
if production_origins := os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend(production_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to needed methods
    allow_headers=["Content-Type", "Authorization"],  # Restrict headers
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )