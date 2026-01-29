"""TruthCheck API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.graph import run_truthcheck


router = APIRouter(prefix="/api/truthcheck", tags=["truthcheck"])


# Request/Response models
class VerifyClaimRequest(BaseModel):
    """Request model for claim verification."""
    claim: str = Field(..., min_length=10, max_length=500, description="Health claim to verify")

    class Config:
        json_schema_extra = {
            "example": {
                "claim": "Does creatine improve muscle strength?"
            }
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
                        "quality_rationale": "High-quality meta-analysis"
                    }
                ],
                "search_queries": [
                    "creatine supplementation muscle strength meta-analysis"
                ],
                "stats": {
                    "studies_found": 12,
                    "studies_scored": 12,
                    "top_studies_count": 5
                }
            }
        }


@router.post("/verify", response_model=VerifyClaimResponse)
async def verify_claim(request: VerifyClaimRequest):
    """Verify a health claim using evidence from PubMed.

    This endpoint orchestrates the full TruthCheck pipeline:
    1. Search Agent: Finds relevant studies from PubMed
    2. Quality Evaluator: Scores and ranks studies
    3. Synthesis Agent: Generates verdict and summary

    Returns:
        Verdict, summary, and supporting evidence
    """
    try:
        # Run the TruthCheck pipeline
        result = await run_truthcheck(request.claim)

        # Check if we got an error
        if result.get("search_error"):
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {result['search_error']}"
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
                quality_rationale=study.get("quality_rationale")
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
                "top_studies_count": len(top_studies)
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "TruthCheck API",
        "version": "1.0.0"
    }
