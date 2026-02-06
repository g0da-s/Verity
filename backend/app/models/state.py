"""LangGraph state schema - data passed between agents in the pipeline."""

from typing import TypedDict, Annotated, List, Optional
from operator import add
from pydantic import BaseModel


class Study(BaseModel):
    """Metadata for a scientific study from PubMed."""

    pubmed_id: str
    title: str
    authors: str
    journal: str
    year: int
    study_type: str
    sample_size: int
    url: str
    abstract: Optional[str] = None
    quality_score: Optional[float] = None
    quality_rationale: Optional[str] = None


class VerityState(TypedDict, total=False):
    """State passed through the agent pipeline. Fields added incrementally by each agent."""

    # Input
    claim: str
    normalized_claim: str

    # Search Agent outputs (Annotated with 'add' appends instead of replaces)
    search_queries: Annotated[List[str], add]
    raw_studies: Annotated[List[Study], add]
    search_error: str

    # Quality Evaluator outputs
    scored_studies: List[Study]
    top_studies: List[Study]

    # Synthesis Agent outputs
    verdict: str
    verdict_emoji: str
    summary: str
