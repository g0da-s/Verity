"""Quick test of Synthesis Agent with mock data."""

import sys
sys.path.insert(0, '/Users/goda/Desktop/CODE/Turing College/gsmulk-AE.3.5/backend')

import asyncio
from app.agents.synthesis_agent import SynthesisAgent
from app.models.state import VerityState, Study


async def test_synthesis_quick():
    """Test Synthesis Agent with a few mock studies."""
    print("🧪 Testing Synthesis Agent (Quick Test)\n")
    print("=" * 80)

    # Mock top studies (just 3 for quick testing)
    mock_studies: list[Study] = [
        {
            "pubmed_id": "12345",
            "title": "Effects of Creatine Supplementation and Resistance Training on Muscle Strength",
            "authors": "Wang Z, Qiu B, Li R, et al.",
            "journal": "Nutrients",
            "year": 2024,
            "study_type": "meta-analysis",
            "sample_size": 1500,
            "abstract": "This meta-analysis examined the effects of creatine supplementation combined with resistance training on muscle strength. Results showed significant improvements in bench press (ES=0.36, p<0.001) and leg press strength (ES=0.42, p<0.001) compared to placebo groups. The effects were consistent across 25 RCTs with 1500 total participants.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
            "quality_score": 9.2,
            "quality_rationale": "High-quality meta-analysis with large sample size"
        },
        {
            "pubmed_id": "67890",
            "title": "Creatine Monohydrate Supplementation on Muscle Strength: A Systematic Review",
            "authors": "Burke R, Piñero A, et al.",
            "journal": "Sports Medicine",
            "year": 2023,
            "study_type": "systematic review",
            "sample_size": 800,
            "abstract": "Systematic review of 18 studies examining creatine supplementation effects on muscle strength in resistance-trained individuals. Results indicate consistent improvements in maximal strength (mean difference: 3.2kg in bench press) and power output. Effects were most pronounced in exercises lasting <30 seconds.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/67890/",
            "quality_score": 8.7,
            "quality_rationale": "Well-conducted systematic review from reputable journal"
        },
        {
            "pubmed_id": "11111",
            "title": "Efficacy of Creatine Supplementation on Muscle Strength in Older Adults",
            "authors": "Dos Santos EEP, et al.",
            "journal": "Age and Ageing",
            "year": 2021,
            "study_type": "meta-analysis",
            "sample_size": 211,
            "abstract": "Meta-analysis of 8 RCTs examining creatine effects in older adults (60+ years). Creatine supplementation combined with resistance training showed moderate improvements in upper-body strength (ES=0.28) and lower-body strength (ES=0.31). Effects were more modest than in younger populations but still statistically significant.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/11111/",
            "quality_score": 7.8,
            "quality_rationale": "Good quality meta-analysis with specific population focus"
        }
    ]

    # Create state
    state: VerityState = {
        "claim": "Does creatine improve muscle strength?",
        "top_studies": mock_studies
    }

    print(f"💬 Claim: {state['claim']}")
    print(f"📚 Studies to analyze: {len(mock_studies)}\n")
    print("=" * 80)

    # Run Synthesis Agent
    synthesizer = SynthesisAgent()
    result = await synthesizer.run(state)

    # Display results
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_synthesis_quick())
