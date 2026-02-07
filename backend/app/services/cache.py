"""Cache service for storing and retrieving verification results."""

import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import CachedResult
from app.utils.normalize import normalize_claim

logger = logging.getLogger(__name__)


async def get_cached_result(db: AsyncSession, claim: str) -> CachedResult | None:
    """Look up a cached result for a claim.

    Returns the cached result if found and not expired, None otherwise.
    Updates last_accessed timestamp on cache hit.
    """
    normalized = normalize_claim(claim)
    logger.debug("Cache lookup for normalized claim")

    result = await db.execute(
        select(CachedResult).where(CachedResult.normalized_claim == normalized)
    )
    cached = result.scalar_one_or_none()

    if cached is None:
        logger.debug("Cache MISS - no entry found")
        return None

    # Check if expired
    if cached.is_expired():
        logger.debug("Cache MISS - entry expired")
        return None

    # Update last_accessed timestamp
    cached.last_accessed = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"Cache HIT (v{cached.version})")
    return cached


async def save_to_cache(
    db: AsyncSession,
    claim: str,
    verdict: str,
    verdict_emoji: str,
    summary: str,
    top_studies: list,
    search_queries: list,
    stats: dict,
    execution_time: float = 0.0,
    ttl_days: int = 30,
) -> CachedResult:
    """Save a verification result to the cache.

    If a cache entry exists for this claim (even if expired), update it.
    Otherwise, create a new entry.
    """
    normalized = normalize_claim(claim)
    logger.debug("Saving to cache")

    # Check if entry already exists
    result = await db.execute(
        select(CachedResult).where(CachedResult.normalized_claim == normalized)
    )
    cached = result.scalar_one_or_none()

    if cached is not None:
        # Update existing entry
        logger.debug(f"Updating existing cache entry (v{cached.version})")
        cached.update_with_fresh_data(
            verdict=verdict,
            verdict_emoji=verdict_emoji,
            summary=summary,
            studies_json=top_studies,
            stats=stats,
            execution_time=execution_time,
            ttl_days=ttl_days,
        )
    else:
        # Create new entry
        logger.debug("Creating new cache entry")
        cached = CachedResult.create_with_ttl(
            days=ttl_days,
            normalized_claim=normalized,
            original_claim=claim,
            verdict=verdict,
            verdict_emoji=verdict_emoji,
            summary=summary,
            studies_json=top_studies,
            stats=stats,
            execution_time=execution_time,
        )
        db.add(cached)

    await db.commit()
    await db.refresh(cached)
    logger.info(f"Cache saved (v{cached.version})")

    return cached
