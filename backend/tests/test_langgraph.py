"""Test LangGraph workflow."""

import sys
sys.path.insert(0, '/Users/goda/Desktop/CODE/Turing College/gsmulk-AE.3.5/backend')

import asyncio
from app.graph import run_verity


async def test_langgraph():
    """Test the LangGraph workflow with a health claim."""
    print("\n" + "="*80)
    print("🧪 TESTING LANGGRAPH WORKFLOW")
    print("="*80)

    claim = "Does creatine improve muscle strength?"
    print(f"\n💬 Testing claim: '{claim}'")
    print("\n" + "="*80 + "\n")

    # Run the workflow
    result = await run_verity(claim)

    # Display final results
    print("\n" + "="*80)
    print("🎯 FINAL RESULTS FROM LANGGRAPH")
    print("="*80)

    print(f"\n📋 Claim: {result.get('claim')}")
    print(f"\n🏆 Verdict: {result.get('verdict_emoji')} {result.get('verdict')}")
    print(f"\n📝 Summary:\n{result.get('summary')}")

    # Stats
    print("\n" + "="*80)
    print("📊 Pipeline Stats:")
    print(f"   - Search queries: {len(result.get('search_queries', []))}")
    print(f"   - Studies found: {len(result.get('raw_studies', []))}")
    print(f"   - Studies scored: {len(result.get('scored_studies', []))}")
    print(f"   - Top studies: {len(result.get('top_studies', []))}")
    print(f"   - Verdict: {result.get('verdict')}")

    print("\n" + "="*80)
    print("✅ LANGGRAPH TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_langgraph())
