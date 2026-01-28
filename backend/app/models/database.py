"""SQLAlchemy database models for caching and tracking."""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

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
    verdict_text = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)  # Full formatted markdown output
    studies_json = Column(JSON, nullable=False)  # List of top studies used

    # Metadata
    num_studies = Column(Integer, nullable=False)
    token_usage = Column(JSON, nullable=False)
    execution_time = Column(Float, nullable=False)  # Seconds

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    cache_expires_at = Column(DateTime, nullable=False)  # Cache TTL

    # Version tracking
    version = Column(Integer, default=1, nullable=False)  # Increment on each update

    def __repr__(self):
        return f"<CachedResult(claim='{self.normalized_claim}', verdict='{self.verdict}', v{self.version})>"

    @classmethod
    def create_with_ttl(cls, days: int = 30, **kwargs):
        """Create a cached result with TTL in days."""
        expires_at = datetime.utcnow() + timedelta(days=days)
        return cls(cache_expires_at=expires_at, **kwargs)

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return datetime.utcnow() > self.cache_expires_at

    def update_with_fresh_data(
        self,
        verdict: str,
        verdict_emoji: str,
        verdict_text: str,
        summary: str,
        studies_json: dict,
        num_studies: int,
        token_usage: dict,
        execution_time: float,
        ttl_days: int = 30
    ):
        """Update expired cache entry with fresh analysis data.

        This preserves the original created_at timestamp and increments
        the version counter, allowing us to track how the evidence has
        changed over time.
        """
        self.verdict = verdict
        self.verdict_emoji = verdict_emoji
        self.verdict_text = verdict_text
        self.summary = summary
        self.studies_json = studies_json
        self.num_studies = num_studies
        self.token_usage = token_usage
        self.execution_time = execution_time
        self.last_updated = datetime.utcnow()
        self.cache_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
        self.version += 1


class SearchLog(Base):
    """Log of all PubMed searches performed."""

    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    claim = Column(String(500), nullable=False)
    normalized_claim = Column(String(500), nullable=False, index=True)
    search_queries = Column(JSON, nullable=False)  # List of PubMed queries used
    num_results = Column(Integer, nullable=False)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<SearchLog(claim='{self.claim}', results={self.num_results})>"


class TokenUsage(Base):
    """Track token usage per agent for cost analysis."""

    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    claim = Column(String(500), nullable=False)
    agent = Column(
        String(50), nullable=False, index=True
    )  # "search", "quality", "synthesis"
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    estimated_cost = Column(Float, nullable=False)  # USD
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<TokenUsage(agent='{self.agent}', tokens={self.total_tokens}, cost=${self.estimated_cost:.4f})>"
