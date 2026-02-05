"""Test Quality Evaluator Agent."""

import asyncio
from app.agents.search_agent import SearchAgent
from app.agents.quality_evaluator import QualityEvaluator
from app.models.state import VerityState


async def test_quality_evaluator():
    """Test Quality Evaluator with real studies from Search Agent."""
    print("🧪 Testing Quality Evaluator Agent\n")
    print("=" * 80)

    # Step 1: Get studies from Search Agent
    print("\n📋 Step 1: Getting studies from Search Agent...")
    search_agent = SearchAgent()
    state: VerityState = {
        "claim": "Does creatine improve muscle strength?"
    }

    search_result = await search_agent.run(state)
    raw_studies = search_result.get("raw_studies", [])
    print(f"   ✅ Got {len(raw_studies)} studies")

    # Step 2: Score and rank with Quality Evaluator
    print("\n📋 Step 2: Scoring studies with Quality Evaluator...")
    evaluator = QualityEvaluator()

    state_with_studies = {
        **search_result,
        "raw_studies": raw_studies
    }

    result = await evaluator.run(state_with_studies)

    # Display final results
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)

    top_studies = result.get("top_studies", [])
    print(f"\n🏆 Top {len(top_studies)} Studies Selected:\n")

    for i, study in enumerate(top_studies, 1):
        score = study.get('quality_score', 0)
        print(f"{i}. [{score:.1f}/10] {study['title']}")
        print(f"   {study['authors']}")
        print(f"   {study['journal']} ({study['year']})")
        print(f"   Type: {study['study_type']}, n={study['sample_size']}")
        print(f"   Rationale: {study.get('quality_rationale', 'N/A')}")
        print(f"   URL: {study['url']}\n")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_quality_evaluator())
