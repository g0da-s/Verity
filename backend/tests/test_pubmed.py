"""Quick test of PubMed tool."""

import asyncio
from app.tools.pubmed import PubMedTool


async def test_pubmed():
    """Test PubMed search and fetch."""
    print("🔬 Testing PubMed API...\n")

    tool = PubMedTool()

    # Test 1: Search
    print("1️⃣ Searching for 'creatine muscle strength'...")
    ids = await tool.search("creatine muscle strength", max_results=5)
    print(f"   Found {len(ids)} studies")
    print(f"   IDs: {ids[:3]}...\n")

    # Test 2: Fetch details
    print("2️⃣ Fetching details for first 3 studies...")
    studies = await tool.fetch_details(ids[:3])
    print(f"   Retrieved {len(studies)} full studies\n")

    # Test 3: Display first study
    if studies:
        study = studies[0]
        print("3️⃣ First study details:")
        print(f"   Title: {study['title'][:80]}...")
        print(f"   Authors: {study['authors']}")
        print(f"   Journal: {study['journal']}")
        print(f"   Year: {study['year']}")
        print(f"   Type: {study['study_type']}")
        print(f"   Sample: n={study['sample_size']}")
        print(f"   URL: {study['url']}")
        print(f"   Abstract: {study['abstract'][:150]}...\n")

    print("✅ PubMed tool working correctly!")


if __name__ == "__main__":
    asyncio.run(test_pubmed())
