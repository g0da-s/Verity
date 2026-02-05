"""LangGraph state schema - data passed between agents.

This module defines the state structure that flows through the 3-agent pipeline:
Search Agent → Quality Evaluator Agent → Synthesis Agent

The state uses TypedDict for type safety and LangGraph's Annotated types
for reducer functions (like appending to lists).
"""

from typing import TypedDict, Annotated, List
from operator import add


class Study(TypedDict, total=False):
    """Metadata for a single scientific study from PubMed.

    total=False allows fields to be optional (added incrementally by agents).
    """

    # Basic metadata (from PubMed)
    pubmed_id: str  # e.g., "12345678"
    title: str
    authors: str  # Comma-separated: "Smith J, Jones K, Williams L"
    journal: str
    year: int
    study_type: str  # "meta-analysis", "rct", "observational", etc.
    sample_size: int
    abstract: str  # Results and Conclusions sections (or full text if unstructured)
    url: str  # https://pubmed.ncbi.nlm.nih.gov/ID/

    # Quality metrics (added by Quality Evaluator Agent)
    quality_score: float  # 0-10 scale
    quality_rationale: str  # Why this score was assigned


class VerityState(TypedDict, total=False):
    """Main state object passed through the agent pipeline.

    Each agent reads from and writes to this shared state.
    Fields are added incrementally as agents process the claim.

    total=False makes all fields optional, allowing incremental updates.
    """

    # ============================================================
    # INPUT (from user, set initially)
    # ============================================================
    claim: str  # Original user input: "Is creatine good?"
    normalized_claim: str  # Cleaned version: "is creatine good"

    # ============================================================
    # SEARCH AGENT OUTPUTS
    # ============================================================
    # Using Annotated with 'add' operator allows appending to lists
    # instead of replacing them (useful for multiple search attempts)
    search_queries: Annotated[List[str], add]  # Generated PubMed queries
    raw_studies: Annotated[List[Study], add]  # All studies found (20-30)
    search_error: str  # Error message if search failed, None otherwise

    # ============================================================
    # QUALITY EVALUATOR AGENT OUTPUTS
    # ============================================================
    scored_studies: List[Study]  # All studies with quality scores added
    top_studies: List[Study]  # Top 8 studies selected for synthesis

    # ============================================================
    # SYNTHESIS AGENT OUTPUTS
    # ============================================================
    verdict: str  # "works", "maybe", "doesnt_work"
    verdict_emoji: str  # "✅", "⚠️", "❌"
    summary: str  # Full formatted markdown output for display
