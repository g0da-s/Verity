"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import truthcheck


# Create FastAPI app
app = FastAPI(
    title="TruthCheck API",
    description="Evidence-based health claim verification using PubMed and Claude AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(truthcheck.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TruthCheck API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/truthcheck/health"
    }


@app.get("/health")
async def health():
    """Global health check."""
    return {"status": "healthy"}
