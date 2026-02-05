"""Quality Evaluator Agent - Scores and ranks studies by quality.

This agent:
1. Takes raw studies from Search Agent
2. Uses Claude to score each study (0-10)
3. Considers: study type, sample size, journal, recency
4. Returns top 5-10 highest quality studies

Ensures only high-quality evidence is used for final verdict.
"""

import json
import re
from typing import List, Dict
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.utils.retry import invoke_with_retry
from app.models.state import VerityState, Study


def _fallback_score(study: Study) -> Dict:
    """Heuristic score used when the LLM call fails or returns unparseable output."""
    score = 5.0
    study_type = study.get("study_type", "").lower()
    if "meta-analysis" in study_type:
        score = 9.0
    elif "systematic review" in study_type:
        score = 7.5
    elif "rct" in study_type or "randomized" in study_type:
        score = 6.5

    if study.get("sample_size", 0) > 1000:
        score += 0.5
    if study.get("year", 2000) >= 2023:
        score += 0.5

    return {
        "quality_score": min(10.0, score),
        "quality_rationale": f"Fallback score based on {study_type} type",
    }


class QualityEvaluator:
    """Agent responsible for scoring and ranking studies by quality.

    Sends all studies in a single LLM call to minimise API round-trips,
    then falls back to heuristic scoring for any study the LLM missed.
    """

    def __init__(self):
        """Initialize Quality Evaluator with Groq Llama."""
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.groq_api_key,
            temperature=0.1,
        )

    async def score_all_studies(self, studies: List[Study]) -> List[Study]:
        """Score all studies in a single LLM call.

        Args:
            studies: List of studies to score

        Returns:
            List of studies with quality_score and quality_rationale added
        """
        if not studies:
            return []

        print(f"\n⚖️  Quality Evaluator: Scoring {len(studies)} studies...")

        system_prompt = """You are a scientific quality assessor. You will be given a numbered list of studies. Score EACH one from 0-10 based on these criteria:

1. Study Type (40% weight):
   - Meta-analysis: 9-10 points
   - Systematic review: 7-8 points
   - RCT: 6-7 points
   - Observational/cohort: 3-5 points
   - Case study/other: 1-3 points

2. Sample Size (30% weight):
   - n > 1000: full points
   - n = 500-1000: good points
   - n = 100-500: moderate points
   - n < 100: low points
   - n = 0 (meta-analysis aggregate): moderate points

3. Journal Quality (20% weight):
   - High-impact journals (Nature, Science, JAMA, BMJ, Lancet): high points
   - Specialized reputable journals: moderate points
   - Other journals: low-moderate points

4. Recency (10% weight):
   - Last 2 years: full points
   - 2-5 years: good points
   - 5-10 years: moderate points
   - 10+ years: low points

OUTPUT: Return a JSON array with one object per study, in the SAME order as the input. Each object must have "score" (number) and "rationale" (1-2 sentences).

Example:
[
  {"score": 8.5, "rationale": "High-quality meta-analysis with large sample."},
  {"score": 6.0, "rationale": "Solid RCT but limited sample size."}
]

Return ONLY the JSON array, no other text."""

        # Build the numbered study list for the user message
        study_lines = []
        for i, study in enumerate(studies, 1):
            study_lines.append(
                f"{i}. Title: {study.get('title', 'N/A')}\n"
                f"   Authors: {study.get('authors', 'N/A')}\n"
                f"   Journal: {study.get('journal', 'N/A')}\n"
                f"   Year: {study.get('year', 'N/A')}\n"
                f"   Type: {study.get('study_type', 'N/A')}\n"
                f"   Sample Size: {study.get('sample_size', 0)}"
            )

        user_prompt = "Score each of these studies:\n\n" + "\n\n".join(study_lines)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await invoke_with_retry(self.llm, messages)
            content = re.sub(r"```(?:json)?\s*|\s*```", "", response.content).strip()
            scores = json.loads(content)

            if not isinstance(scores, list):
                raise ValueError("Response is not a JSON array")

            # Map scores back onto studies; fall back per-study if the array is short
            scored_studies = []
            for i, study in enumerate(studies):
                if i < len(scores) and isinstance(scores[i], dict):
                    scored_studies.append(
                        {
                            **study,
                            "quality_score": float(scores[i].get("score", 0)),
                            "quality_rationale": scores[i].get(
                                "rationale", "No rationale provided"
                            ),
                        }
                    )
                else:
                    scored_studies.append({**study, **_fallback_score(study)})

            print(f"   Scored {len(scored_studies)}/{len(studies)} studies")
            return scored_studies

        except Exception as e:
            print(f"⚠️  Batch scoring failed, using fallback for all studies: {e}")
            return [{**study, **_fallback_score(study)} for study in studies]

    def rank_studies(self, scored_studies: List[Study], top_n: int = 5) -> List[Study]:
        """Rank studies by quality score and return top N.

        Args:
            scored_studies: Studies with quality_score field
            top_n: Number of top studies to return (default: 5)

        Returns:
            Top N studies sorted by quality_score (descending)
        """
        # Sort by quality_score (descending)
        ranked = sorted(
            scored_studies, key=lambda s: s.get("quality_score", 0), reverse=True
        )

        return ranked[:top_n]

    async def run(self, state: VerityState) -> VerityState:
        """Execute Quality Evaluator node in LangGraph workflow.

        Args:
            state: Current graph state with 'raw_studies' field

        Returns:
            Updated state with scored_studies and top_studies added
        """
        raw_studies = state.get("raw_studies", [])

        if not raw_studies:
            print("⚠️  No studies to evaluate")
            return {**state, "scored_studies": [], "top_studies": []}

        try:
            # Step 1: Score all studies
            scored_studies = await self.score_all_studies(raw_studies)

            # Step 2: Rank and select top studies
            top_studies = self.rank_studies(scored_studies, top_n=5)

            # Step 3: Display results
            print(f"\n🏆 Top {len(top_studies)} Studies:")
            for i, study in enumerate(top_studies, 1):
                score = study.get("quality_score", 0)
                print(f"\n   {i}. [{score:.1f}/10] {study['title'][:80]}...")
                print(f"      {study['authors']} ({study['year']})")
                print(f"      Type: {study['study_type']}, n={study['sample_size']}")
                print(f"      Rationale: {study.get('quality_rationale', 'N/A')[:100]}")

            # Return updated state
            return {
                **state,
                "scored_studies": scored_studies,
                "top_studies": top_studies,
            }

        except Exception as e:
            print(f"❌ Quality Evaluator failed: {e}")
            # Return studies unscored if evaluation fails
            return {
                **state,
                "scored_studies": raw_studies,
                "top_studies": raw_studies[:10],
            }


# Node function for LangGraph
async def quality_evaluator_node(state: VerityState) -> VerityState:
    """LangGraph node wrapper for Quality Evaluator.

    This function is called by LangGraph during workflow execution.
    """
    evaluator = QualityEvaluator()
    return await evaluator.run(state)
