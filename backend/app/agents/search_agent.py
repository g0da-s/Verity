"""Search Agent - Finds relevant scientific studies from PubMed.

This agent:
1. Generates optimized PubMed search queries using Claude
2. Executes searches via PubMed E-utilities API
3. Returns raw studies for quality evaluation

Designed to find high-quality evidence: meta-analyses, RCTs, systematic reviews.
"""

import asyncio
from typing import List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.models.state import VerityState
from app.tools.pubmed import PubMedTool
from app.utils.retry import invoke_with_retry


class SearchAgent:
    """Agent responsible for finding relevant PubMed studies.

    Uses Claude to generate optimized search queries, then fetches studies
    from PubMed. Prioritizes high-quality study types (meta-analyses, RCTs).
    """

    def __init__(self):
        """Initialize Search Agent with Groq Llama."""
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.groq_api_key,
            temperature=0.3,
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
        system_prompt = """You are a PubMed search expert. Generate 2-3 optimized search queries to find high-quality evidence about a health claim.

PUBMED QUERY RULES:
1. Keep queries SHORT and focused (3-5 key terms)
2. Use ONE study type per query (meta-analysis, systematic review, or RCT)
3. NEVER use OR within a query - it causes unexpected results
4. Use PubMed field tags for precision:
   - [Title/Abstract] for key terms
   - [pt] for publication types (meta-analysis[pt], randomized controlled trial[pt])
5. Use scientific terminology (e.g., "resistance training" not "working out")

GOOD EXAMPLES:
- creatine muscle strength meta-analysis[pt]
- creatine supplementation resistance training randomized controlled trial[pt]
- vitamin D bone density systematic review[pt]

BAD EXAMPLES (avoid these patterns):
- creatine meta-analysis OR systematic review (OR causes issues)
- creatine supplementation muscle strength gains ergogenic effect (too many terms)

OUTPUT FORMAT (JSON only, no explanation):
{
  "queries": [
    "query 1",
    "query 2",
    "query 3"
  ]
}"""

        user_prompt = f"""Health claim: "{claim}"

Generate 2-3 PubMed search queries to find the best scientific evidence about this claim."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await invoke_with_retry(self.llm, messages)

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

    async def run(self, state: VerityState) -> VerityState:
        """Execute Search Agent node in LangGraph workflow.

        Args:
            state: Current graph state with 'claim' field

        Returns:
            Updated state with search_queries and raw_studies added
        """
        claim = state.get("claim", "")

        if not claim:
            return {**state, "search_error": "No claim provided"}

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
                    print(
                        f"      Type: {study['study_type']}, n={study['sample_size']}"
                    )

            # Return updated state
            # Note: search_queries and raw_studies use 'add' operator, so they append
            return {
                **state,
                "search_queries": queries,
                "raw_studies": studies,
                "search_error": None if studies else "No studies found",
            }

        except Exception as e:
            print(f"❌ Search Agent failed: {e}")
            return {**state, "search_error": str(e)}


# Node function for LangGraph
async def search_node(state: VerityState) -> VerityState:
    """LangGraph node wrapper for Search Agent.

    This function is called by LangGraph during workflow execution.
    """
    agent = SearchAgent()
    return await agent.run(state)
