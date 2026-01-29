"""Test the full 3-agent pipeline: Search → Quality → Synthesis."""

import sys
sys.path.insert(0, '/Users/goda/Desktop/CODE/Turing College/gsmulk-AE.3.5/backend')

import asyncio
from app.agents.search_agent import SearchAgent
from app.agents.quality_evaluator import QualityEvaluator
from app.agents.synthesis_agent import SynthesisAgent
from app.models.state import TruthCheckState


async def test_full_pipeline():
    """Test complete TruthCheck pipeline with all 3 agents."""
    print("\n" + "="*80)
    print("🧪 TESTING FULL TRUTHCHECK PIPELINE")
    print("="*80)

    # Initial state
    state: TruthCheckState = {
        "claim": "Does creatine improve muscle strength?"
    }

    print(f"\n💬 User Claim: '{state['claim']}'")
    print("\n" + "="*80)

    # AGENT 1: Search Agent
    print("\n🔍 AGENT 1: SEARCH AGENT")
    print("="*80)
    search_agent = SearchAgent()
    state = await search_agent.run(state)

    raw_studies_count = len(state.get("raw_studies", []))
    queries_count = len(state.get("search_queries", []))
    print(f"\n✅ Search Complete: {queries_count} queries → {raw_studies_count} studies found")

    # AGENT 2: Quality Evaluator
    print("\n" + "="*80)
    print("⚖️  AGENT 2: QUALITY EVALUATOR")
    print("="*80)
    evaluator = QualityEvaluator()
    state = await evaluator.run(state)

    top_studies_count = len(state.get("top_studies", []))
    print(f"\n✅ Quality Evaluation Complete: Top {top_studies_count} studies selected")

    # AGENT 3: Synthesis Agent
    print("\n" + "="*80)
    print("🔬 AGENT 3: SYNTHESIS AGENT")
    print("="*80)
    synthesizer = SynthesisAgent()
    state = await synthesizer.run(state)

    # Final Results
    print("\n" + "="*80)
    print("🎯 FINAL RESULTS")
    print("="*80)

    print(f"\n📋 Claim: {state.get('claim')}")
    print(f"\n🏆 Verdict: {state.get('verdict_emoji')} {state.get('verdict')}")
    print(f"\n📝 Summary:\n{state.get('summary')}")

    print("\n" + "="*80)
    print("✅ PIPELINE TEST COMPLETE")
    print("="*80)

    # Display stats
    print("\n📊 Pipeline Stats:")
    print(f"   - Queries generated: {queries_count}")
    print(f"   - Studies found: {raw_studies_count}")
    print(f"   - Studies scored: {raw_studies_count}")
    print(f"   - Top studies used: {top_studies_count}")
    print(f"   - Final verdict: {state.get('verdict')}")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
