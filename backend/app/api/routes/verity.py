"""Verity API endpoints."""

import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph import run_verity
from app.db.session import get_db
from app.services.cache import get_cached_result, save_to_cache
from app.services.claim_validator import validate_claim, ClaimValidationError
from app.utils.retry import RateLimitExceeded
from app.utils.rate_limit import rate_limit


router = APIRouter(prefix="/api/verity", tags=["verity"])


# Request/Response models
class VerifyClaimRequest(BaseModel):
    """Request model for claim verification."""

    claim: str = Field(
        ..., min_length=10, max_length=500, description="Health claim to verify"
    )

    class Config:
        json_schema_extra = {
            "example": {"claim": "Does creatine improve muscle strength?"}
        }


class Study(BaseModel):
    """Study model for response."""

    pubmed_id: str
    title: str
    authors: str
    journal: str
    year: int
    study_type: str
    sample_size: int
    url: str
    quality_score: Optional[float] = None
    quality_rationale: Optional[str] = None


class VerifyClaimResponse(BaseModel):
    """Response model for claim verification."""

    claim: str
    verdict: str
    verdict_emoji: str
    summary: str
    top_studies: List[Study]
    search_queries: List[str]
    stats: dict
    cache_hit: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "claim": "Does creatine improve muscle strength?",
                "verdict": "Strongly Supported",
                "verdict_emoji": "✅",
                "summary": "Creatine supplementation combined with resistance training...",
                "top_studies": [
                    {
                        "pubmed_id": "12345",
                        "title": "Effects of Creatine...",
                        "authors": "Wang Z, et al.",
                        "journal": "Nutrients",
                        "year": 2024,
                        "study_type": "meta-analysis",
                        "sample_size": 1500,
                        "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
                        "quality_score": 9.2,
                        "quality_rationale": "High-quality meta-analysis",
                    }
                ],
                "search_queries": [
                    "creatine supplementation muscle strength meta-analysis"
                ],
                "stats": {
                    "studies_found": 12,
                    "studies_scored": 12,
                    "top_studies_count": 5,
                },
                "cache_hit": False,
            }
        }


@router.post(
    "/verify", response_model=VerifyClaimResponse, dependencies=[Depends(rate_limit)]
)
async def verify_claim(request: VerifyClaimRequest, db: AsyncSession = Depends(get_db)):
    """Verify a health claim using evidence from PubMed.

    This endpoint first validates the claim is specific enough, then checks
    the cache for a recent result. If not found or expired, it orchestrates
    the full Verity pipeline:
    1. Search Agent: Finds relevant studies from PubMed
    2. Quality Evaluator: Scores and ranks studies
    3. Synthesis Agent: Generates verdict and summary

    Returns:
        Verdict, summary, and supporting evidence

    Raises:
        400: If the claim is too vague (includes suggestions)
    """
    try:
        # Validate claim is specific enough
        try:
            await validate_claim(request.claim)
        except ClaimValidationError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Claim is too vague",
                    "message": e.message,
                    "suggestions": e.suggestions,
                },
            )

        # Check cache first
        cached = await get_cached_result(db, request.claim)
        if cached is not None:
            # Return cached result
            top_studies = [Study(**study) for study in cached.studies_json]
            return VerifyClaimResponse(
                claim=cached.original_claim,
                verdict=cached.verdict,
                verdict_emoji=cached.verdict_emoji,
                summary=cached.summary,
                top_studies=top_studies,
                search_queries=[],  # Not stored in cache
                stats=cached.stats,
                cache_hit=True,
            )

        # Cache miss - run the Verity pipeline
        start_time = time.time()
        print(f"🚀 Starting pipeline for: {request.claim}")
        result = await run_verity(request.claim)
        print(f"✅ Pipeline complete. Result keys: {list(result.keys())}")
        print(f"   raw_studies: {result.get('raw_studies')} (type: {type(result.get('raw_studies'))})")
        print(f"   search_error: {result.get('search_error')}")
        execution_time = time.time() - start_time

        # Check if we got an error
        if result.get("search_error"):
            print(f"❌ Search error detected: {result.get('search_error')}")
            raise HTTPException(
                status_code=500, detail=f"Search failed: {result['search_error']}"
            )

        # Handle case where no studies were found
        print(f"🔍 Checking raw_studies: bool={bool(result.get('raw_studies'))}")
        if not result.get("raw_studies"):
            print(f"📭 No studies found - returning early")
            return VerifyClaimResponse(
                claim=result.get("claim", request.claim),
                verdict="Inconclusive",
                verdict_emoji="🔍",
                summary="No peer-reviewed studies were found on PubMed for this specific topic. This doesn't mean the claim is false — it may just be too new, too specific, or not yet well-researched. Try rephrasing with broader terms.",
                top_studies=[],
                search_queries=result.get("search_queries", []),
                stats={
                    "studies_found": 0,
                    "studies_scored": 0,
                    "top_studies_count": 0,
                },
                cache_hit=False,
            )

        # Format top studies for response
        top_studies = [
            Study(
                pubmed_id=study["pubmed_id"],
                title=study["title"],
                authors=study["authors"],
                journal=study["journal"],
                year=study["year"],
                study_type=study["study_type"],
                sample_size=study["sample_size"],
                url=study["url"],
                quality_score=study.get("quality_score"),
                quality_rationale=study.get("quality_rationale"),
            )
            for study in result.get("top_studies", [])
        ]

        # Build response
        response = VerifyClaimResponse(
            claim=result["claim"],
            verdict=result.get("verdict", "Inconclusive"),
            verdict_emoji=result.get("verdict_emoji", "❓"),
            summary=result.get("summary", "No summary available"),
            top_studies=top_studies,
            search_queries=result.get("search_queries", []),
            stats={
                "studies_found": len(result.get("raw_studies", [])),
                "studies_scored": len(result.get("scored_studies", [])),
                "top_studies_count": len(top_studies),
            },
            cache_hit=False,
        )

        # Save to cache
        await save_to_cache(
            db=db,
            claim=request.claim,
            verdict=response.verdict,
            verdict_emoji=response.verdict_emoji,
            summary=response.summary,
            top_studies=[study.model_dump() for study in top_studies],
            search_queries=response.search_queries,
            stats=response.stats,
            execution_time=execution_time,
        )

        return response

    except HTTPException:
        raise
    except RateLimitExceeded:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Verity is temporarily unavailable due to high demand. Please try again in about a minute.",
                "retry_after": 60,
            },
        )
    except Exception as e:
        print(f"❌ Unhandled error in /verify: {e}")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Verity API", "version": "1.0.0"}
