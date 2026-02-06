"""FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Must load .env before importing anything that reads env vars
load_dotenv(override=True)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.api import verity  # noqa: E402
from app.models.database import Base  # noqa: E402


def setup_logging():
    log_level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Silence noisy third-party libraries
    for lib in ["httpx", "httpcore", "urllib3", "sqlalchemy.engine"]:
        logging.getLogger(lib).setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Verity API...")
    Path("data").mkdir(exist_ok=True)

    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    logger.info("Verity API ready")
    yield
    logger.info("Shutting down Verity API...")


app = FastAPI(
    title="Verity API",
    description="Evidence-based health claim verification using PubMed and Groq AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(verity.router)


@app.get("/")
async def root():
    return {
        "message": "Verity API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/verity/health",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
