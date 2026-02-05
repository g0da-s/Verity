"""Test Search Agent with a sample health claim."""

import asyncio
from app.agents.search_agent import SearchAgent
from app.models.state import VerityState


async def test_search_agent():
    """Test Search Agent with a real query."""
    print("🧪 Testing Search Agent\n")
    print("=" * 60)

    agent = SearchAgent()

    # Test state
    state: VerityState = {
        "claim": "Does creatine improve muscle strength?"
    }

    print(f"\n📋 Input claim: {state['claim']}")
    print("\n" + "=" * 60)

    # Run agent
    result = await agent.run(state)

    # Display results
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)

    if result.get("search_error"):
        print(f"❌ Error: {result['search_error']}")
    else:
        print(f"\n✅ Success!")
        print(f"\n📝 Generated Queries ({len(result.get('search_queries', []))}):")
        for i, q in enumerate(result.get("search_queries", []), 1):
            print(f"   {i}. {q}")

        print(f"\n📚 Found Studies: {len(result.get('raw_studies', []))}")

        # Show top 5 studies
        studies = result.get("raw_studies", [])
        if studies:
            print("\n🔬 Top 5 Studies:")
            for i, study in enumerate(studies[:5], 1):
                print(f"\n   {i}. {study['title'][:100]}")
                print(f"      Authors: {study['authors']}")
                print(f"      Journal: {study['journal']}")
                print(f"      Year: {study['year']}, Type: {study['study_type']}, n={study['sample_size']}")
                print(f"      URL: {study['url']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_search_agent())
