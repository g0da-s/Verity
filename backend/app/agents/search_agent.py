"""Search Agent - Finds relevant scientific studies from PubMed.

This agent:
1. Generates optimized PubMed search queries using Claude
2. Executes searches via PubMed E-utilities API
3. Returns raw studies for quality evaluation

Designed to find high-quality evidence: meta-analyses, RCTs, systematic reviews.
"""

import asyncio
from typing import List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.models.state import TruthCheckState
from app.tools.pubmed import PubMedTool


class SearchAgent:
    """Agent responsible for finding relevant PubMed studies.

    Uses Claude to generate optimized search queries, then fetches studies
    from PubMed. Prioritizes high-quality study types (meta-analyses, RCTs).
    """

    def __init__(self):
        """Initialize Search Agent with Claude Sonnet 4.5."""
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            api_key=settings.anthropic_api_key,
            temperature=0.3  # Slightly creative for query generation
        )
        self.pubmed = PubMedTool()

    async def generate_queries(self, claim: str) -> List[str]:
        """Generate 2-3 optimized PubMed search queries for a health claim.

        Args:
            claim: User's health claim (e.g., "Is creatine good?")

        Returns:
            List of 2-3 PubMed search queries optimized for finding quality evidence

        Example:
            Input: "Does creatine improve strength?"
            Output: [
                "creatine supplementation muscle strength meta-analysis",
                "creatine monohydrate resistance training randomized controlled trial",
                "creatine ergogenic aid systematic review"
            ]
        """
        system_prompt = """You are a scientific research expert. Generate 2-3 optimized PubMed search queries to find high-quality evidence about a health claim.

REQUIREMENTS:
- Prioritize meta-analyses, systematic reviews, and RCTs
- Use medical/scientific terminology
- Include study type keywords (meta-analysis, systematic review, randomized controlled trial, RCT)
- Keep queries focused and specific
- Avoid overly broad terms

OUTPUT FORMAT (JSON):
{
  "queries": [
    "query 1 here",
    "query 2 here",
    "query 3 here"
  ]
}"""

        user_prompt = f"""Health claim: "{claim}"

Generate 2-3 PubMed search queries to find the best scientific evidence about this claim."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = await self.llm.ainvoke(messages)

            # Parse JSON response
            import json
            # Extract JSON from response (handle potential markdown code blocks)
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            queries = result.get("queries", [])

            # Fallback if parsing fails
            if not queries:
                queries = [f"{claim} meta-analysis systematic review"]

            return queries[:3]  # Max 3 queries

        except Exception as e:
            # Fallback query if LLM fails
            print(f"Query generation failed: {e}")
            return [f"{claim} meta-analysis", f"{claim} systematic review"]

    async def search_studies(self, queries: List[str], max_per_query: int = 6) -> List:
        """Execute PubMed searches for all queries in parallel.

        Args:
            queries: List of search queries
            max_per_query: Maximum results per query (default: 6)

        Returns:
            List of Study objects with metadata
        """
        # Execute all searches in parallel
        tasks = [
            self.pubmed.search_and_fetch(query, max_results=max_per_query)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and deduplicate by pubmed_id
        all_studies = []
        seen_ids = set()

        for result in results:
            if isinstance(result, list):  # Skip exceptions
                for study in result:
                    if study["pubmed_id"] not in seen_ids:
                        all_studies.append(study)
                        seen_ids.add(study["pubmed_id"])

        return all_studies

    async def run(self, state: TruthCheckState) -> TruthCheckState:
        """Execute Search Agent node in LangGraph workflow.

        Args:
            state: Current graph state with 'claim' field

        Returns:
            Updated state with search_queries and raw_studies added
        """
        claim = state.get("claim", "")

        if not claim:
            return {
                **state,
                "search_error": "No claim provided"
            }

        try:
            print(f"\n🔍 Search Agent: Analyzing claim '{claim}'")

            # Step 1: Generate optimized queries
            print("📝 Generating PubMed search queries...")
            queries = await self.generate_queries(claim)
            print(f"   Generated {len(queries)} queries:")
            for i, q in enumerate(queries, 1):
                print(f"   {i}. {q}")

            # Step 2: Execute searches
            print("\n🔬 Searching PubMed...")
            studies = await self.search_studies(queries)
            print(f"   Found {len(studies)} unique studies")

            # Step 3: Display sample results
            if studies:
                print("\n📚 Sample studies:")
                for i, study in enumerate(studies[:3], 1):
                    print(f"   {i}. {study['title'][:80]}...")
                    print(f"      {study['authors']} ({study['year']})")
                    print(f"      Type: {study['study_type']}, n={study['sample_size']}")

            # Return updated state
            # Note: search_queries and raw_studies use 'add' operator, so they append
            return {
                **state,
                "search_queries": queries,
                "raw_studies": studies,
                "search_error": None if studies else "No studies found"
            }

        except Exception as e:
            print(f"❌ Search Agent failed: {e}")
            return {
                **state,
                "search_error": str(e)
            }


# Node function for LangGraph
async def search_node(state: TruthCheckState) -> TruthCheckState:
    """LangGraph node wrapper for Search Agent.

    This function is called by LangGraph during workflow execution.
    """
    agent = SearchAgent()
    return await agent.run(state)
