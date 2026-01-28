"""Initialize the database with all tables."""

import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.database import Base
from app.config import settings


async def init_db():
    """Create all database tables if they don't exist."""

    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    print(f"🔧 Initializing database at: {settings.database_url}")

    # Create engine
    engine = create_async_engine(settings.database_url, echo=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()

    print("\n✅ Database initialized successfully!")
    print(f"📁 Database file: {settings.database_url}")
    print("📊 Tables created:")
    print("   - cached_results")
    print("   - search_logs")
    print("   - token_usage")


if __name__ == "__main__":
    print("🚀 Starting database initialization...\n")
    asyncio.run(init_db())
