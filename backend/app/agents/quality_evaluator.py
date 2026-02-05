"""Quality Evaluator Agent - Scores and ranks studies by quality.

This agent:
1. Takes raw studies from Search Agent
2. Uses Claude to score each study (0-10)
3. Considers: study type, sample size, journal, recency
4. Returns top 5-10 highest quality studies

Ensures only high-quality evidence is used for final verdict.
"""

import asyncio
from typing import List, Dict
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.models.state import VerityState, Study


class QualityEvaluator:
    """Agent responsible for scoring and ranking studies by quality.

    Uses Claude to evaluate each study on multiple criteria and returns
    only the highest quality evidence for synthesis.
    """

    def __init__(self):
        """Initialize Quality Evaluator with Claude Sonnet 4.5."""
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            api_key=settings.anthropic_api_key,
            temperature=0.1  # Low temperature for consistent scoring
        )

    async def score_study(self, study: Study) -> Dict:
        """Score a single study using Claude.

        Args:
            study: Study dictionary with metadata

        Returns:
            Dict with quality_score (float) and quality_rationale (str)
        """
        system_prompt = """You are a scientific quality assessor. Score this study from 0-10 based on:

CRITERIA:
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

OUTPUT FORMAT (JSON):
{
  "score": 8.5,
  "rationale": "Brief 1-2 sentence explanation"
}"""

        user_prompt = f"""Study Details:
- Title: {study.get('title', 'N/A')}
- Authors: {study.get('authors', 'N/A')}
- Journal: {study.get('journal', 'N/A')}
- Year: {study.get('year', 'N/A')}
- Type: {study.get('study_type', 'N/A')}
- Sample Size: {study.get('sample_size', 0)}

Score this study from 0-10."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = await self.llm.ainvoke(messages)

            # Parse JSON response
            import json
            import re
            content = response.content

            # Extract JSON from markdown code blocks if present
            content = re.sub(r'```(?:json)?\s*|\s*```', '', content).strip()

            result = json.loads(content)

            return {
                "quality_score": float(result.get("score", 0)),
                "quality_rationale": result.get("rationale", "No rationale provided")
            }

        except Exception as e:
            # Fallback scoring if Claude fails
            print(f"⚠️  Scoring failed for study, using fallback: {e}")

            # Simple fallback scoring
            score = 5.0  # Default moderate score

            # Study type bonus
            study_type = study.get('study_type', '').lower()
            if 'meta-analysis' in study_type:
                score = 9.0
            elif 'systematic review' in study_type:
                score = 7.5
            elif 'rct' in study_type or 'randomized' in study_type:
                score = 6.5

            # Sample size bonus
            sample_size = study.get('sample_size', 0)
            if sample_size > 1000:
                score += 0.5

            # Recency bonus
            year = study.get('year', 2000)
            if year >= 2023:
                score += 0.5

            score = min(10.0, score)  # Cap at 10

            return {
                "quality_score": score,
                "quality_rationale": f"Fallback score based on {study_type} type"
            }

    async def score_all_studies(self, studies: List[Study], max_concurrent: int = 5) -> List[Study]:
        """Score all studies with concurrency limit.

        Args:
            studies: List of studies to score
            max_concurrent: Max concurrent API calls (default: 5)

        Returns:
            List of studies with quality_score and quality_rationale added
        """
        if not studies:
            return []

        print(f"\n⚖️  Quality Evaluator: Scoring {len(studies)} studies...")

        # Process in batches to avoid rate limits
        scored_studies = []

        for i in range(0, len(studies), max_concurrent):
            batch = studies[i:i + max_concurrent]

            # Score batch in parallel
            tasks = [self.score_study(study) for study in batch]
            scores = await asyncio.gather(*tasks)

            # Add scores to studies
            for study, score_data in zip(batch, scores):
                scored_study = {**study, **score_data}
                scored_studies.append(scored_study)

            print(f"   Scored {min(i + max_concurrent, len(studies))}/{len(studies)} studies...")

        return scored_studies

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
            scored_studies,
            key=lambda s: s.get('quality_score', 0),
            reverse=True
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
            return {
                **state,
                "scored_studies": [],
                "top_studies": []
            }

        try:
            # Step 1: Score all studies
            scored_studies = await self.score_all_studies(raw_studies)

            # Step 2: Rank and select top studies
            top_studies = self.rank_studies(scored_studies, top_n=5)

            # Step 3: Display results
            print(f"\n🏆 Top {len(top_studies)} Studies:")
            for i, study in enumerate(top_studies, 1):
                score = study.get('quality_score', 0)
                print(f"\n   {i}. [{score:.1f}/10] {study['title'][:80]}...")
                print(f"      {study['authors']} ({study['year']})")
                print(f"      Type: {study['study_type']}, n={study['sample_size']}")
                print(f"      Rationale: {study.get('quality_rationale', 'N/A')[:100]}")

            # Return updated state
            return {
                **state,
                "scored_studies": scored_studies,
                "top_studies": top_studies
            }

        except Exception as e:
            print(f"❌ Quality Evaluator failed: {e}")
            # Return studies unscored if evaluation fails
            return {
                **state,
                "scored_studies": raw_studies,
                "top_studies": raw_studies[:10]
            }


# Node function for LangGraph
async def quality_evaluator_node(state: VerityState) -> VerityState:
    """LangGraph node wrapper for Quality Evaluator.

    This function is called by LangGraph during workflow execution.
    """
    evaluator = QualityEvaluator()
    return await evaluator.run(state)
