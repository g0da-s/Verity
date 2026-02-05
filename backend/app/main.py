"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env with override=True so it wins over any shell env vars
# (e.g. LANGSMITH_PROJECT=langchain-academy from LangChain Academy).
# Must happen before anything reads os.environ or imports LangChain.
load_dotenv(override=True)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.api.routes import verity  # noqa: E402
from app.models.database import Base  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)

    # Create tables if they don't exist
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    yield


# Create FastAPI app
app = FastAPI(
    title="Verity API",
    description="Evidence-based health claim verification using PubMed and Claude AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Include routers
app.include_router(verity.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Verity API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/verity/health",
    }


@app.get("/health")
async def health():
    """Global health check."""
    return {"status": "healthy"}
