"""SQLAlchemy database models for caching and tracking."""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta, timezone

Base = declarative_base()


class CachedResult(Base):
    """Cached verification results for health claims.

    Cache entries expire after 30 days. When expired, they are updated
    with fresh analysis rather than deleted, preserving historical data.
    """

    __tablename__ = "cached_results"

    id = Column(Integer, primary_key=True, index=True)
    normalized_claim = Column(String(500), unique=True, index=True, nullable=False)
    original_claim = Column(String(500), nullable=False)

    # Result data
    verdict = Column(String(50), nullable=False)  # "works", "maybe", "doesnt_work"
    verdict_emoji = Column(String(10), nullable=False)
    summary = Column(Text, nullable=False)  # Full formatted markdown output
    studies_json = Column(JSON, nullable=False)  # List of top studies used

    # Metadata
    stats = Column(
        JSON, nullable=False
    )  # {"studies_found": N, "studies_scored": N, "top_studies_count": N}
    execution_time = Column(Float, nullable=False)  # Seconds

    # Timestamps
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_accessed = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_updated = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    cache_expires_at = Column(DateTime, nullable=False)  # Cache TTL

    # Version tracking
    version = Column(Integer, default=1, nullable=False)  # Increment on each update

    def __repr__(self):
        return f"<CachedResult(claim='{self.normalized_claim}', verdict='{self.verdict}', v{self.version})>"

    @classmethod
    def create_with_ttl(cls, days: int = 30, **kwargs):
        """Create a cached result with TTL in days."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)
        return cls(cache_expires_at=expires_at, **kwargs)

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        # SQLite strips timezone info on read — re-attach UTC before comparing
        expires_at = (
            self.cache_expires_at.replace(tzinfo=timezone.utc)
            if self.cache_expires_at.tzinfo is None
            else self.cache_expires_at
        )
        return datetime.now(timezone.utc) > expires_at

    def update_with_fresh_data(
        self,
        verdict: str,
        verdict_emoji: str,
        summary: str,
        studies_json: dict,
        stats: dict,
        execution_time: float,
        ttl_days: int = 30,
    ):
        """Update expired cache entry with fresh analysis data.

        This preserves the original created_at timestamp and increments
        the version counter, allowing us to track how the evidence has
        changed over time.
        """
        self.verdict = verdict
        self.verdict_emoji = verdict_emoji
        self.summary = summary
        self.studies_json = studies_json
        self.stats = stats
        self.execution_time = execution_time
        self.last_updated = datetime.now(timezone.utc)
        self.cache_expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)
        self.version += 1
