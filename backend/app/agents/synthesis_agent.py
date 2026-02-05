"""Synthesis Agent - Generates final verdict and evidence-based summary.

This agent:
1. Takes top-quality studies from Quality Evaluator
2. Analyzes study findings and abstracts
3. Generates verdict: Supported/Not Supported/Inconclusive
4. Creates evidence-based summary with citations

Final step in the Verity pipeline.
"""

from typing import List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.models.state import VerityState, Study
from app.utils.retry import invoke_with_retry


class SynthesisAgent:
    """Agent responsible for generating final verdict and summary.

    Uses Claude to analyze study findings and synthesize evidence-based
    conclusions about health claims.
    """

    def __init__(self):
        """Initialize Synthesis Agent with Groq Llama."""
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.groq_api_key,
            temperature=0.2,
        )

    def prepare_studies_context(self, studies: List[Study]) -> str:
        """Format studies into context for Claude.

        Args:
            studies: List of top-quality studies

        Returns:
            Formatted string with study details
        """
        context_parts = []

        for i, study in enumerate(studies, 1):
            score = study.get("quality_score", 0)
            context = f"""
Study {i} [Quality: {score:.1f}/10]:
- Title: {study.get("title", "N/A")}
- Authors: {study.get("authors", "N/A")}
- Journal: {study.get("journal", "N/A")} ({study.get("year", "N/A")})
- Study Type: {study.get("study_type", "N/A")}
- Sample Size: n={study.get("sample_size", 0)}
- Abstract: {study.get("abstract", "N/A")}
- URL: {study.get("url", "N/A")}
"""
            context_parts.append(context.strip())

        return "\n\n".join(context_parts)

    async def synthesize_verdict(self, claim: str, studies: List[Study]) -> dict:
        """Generate verdict and summary based on studies.

        Args:
            claim: Original health claim
            studies: Top-quality studies to analyze

        Returns:
            Dict with verdict, verdict_emoji, and summary
        """
        studies_context = self.prepare_studies_context(studies)

        system_prompt = """You are a health science communicator who explains research to everyday people. Analyze the provided studies and generate a comprehensive, easy-to-read verdict about a health claim.

STEP 1 - RELEVANCE CHECK:
Before analyzing, check if each study is actually relevant to the claim. Ignore irrelevant studies completely. If NO studies are relevant, verdict is "Inconclusive".

STEP 2 - DETERMINE VERDICT:
- "Strongly Supported" ✅ - Multiple meta-analyses/RCTs show consistent positive evidence
- "Supported" ✓ - Good quality studies show positive evidence
- "Partially Supported" ⚖️ - Mixed evidence or limited scope
- "Inconclusive" ❓ - Insufficient evidence or conflicting results
- "Not Supported" ❌ - Quality studies show no benefit
- "Contradicted" 🚫 - Strong evidence contradicts the claim

STEP 3 - WRITE EACH SECTION:

bottom_line: One clear, direct sentence. Does it work or not? Be honest about uncertainty.

what_research_found: 3-4 bullet points. Each one starts with "•". Include specific numbers (sample sizes, effect sizes, percentages). Cite naturally: "A 2023 meta-analysis of 7,582 people found..." State whether findings were consistent or conflicting.

who_benefits_most: 2-3 bullet points starting with "•". Which populations showed the strongest effects? Who might NOT benefit?

dosage_and_timing: 2-3 bullet points starting with "•". What doses were studied? When to take it? How long until effects? If not applicable to this claim, set this to null.

important_caveats: 2-3 bullet points starting with "•". Key limitations of the research. Safety concerns or interactions. When to see a doctor.

GROUNDING RULES (critical — this is a health tool):
1. ONLY state facts that appear in the provided study abstracts. Do NOT invent dosages, effect sizes, percentages, or study details.
2. If a piece of information is not mentioned in the studies (e.g. dosage, long-term effects, a specific population), say "not reported in these studies" — do not guess.
3. Set dosage_and_timing to null if no study mentions dosage or timing.

WRITING RULES:
1. Write like explaining to a smart friend - NO academic jargon
2. Use "you" and "your" to make it personal
3. Include specific numbers only when they appear in the provided abstracts
4. Be honest about limitations - don't oversell
5. Keep sentences short and punchy

OUTPUT FORMAT (JSON only, no explanation):
{
  "verdict": "verdict category",
  "verdict_emoji": "emoji",
  "bottom_line": "one sentence",
  "what_research_found": "• finding 1\n• finding 2\n• finding 3",
  "who_benefits_most": "• point 1\n• point 2",
  "dosage_and_timing": "• point 1\n• point 2" or null,
  "important_caveats": "• point 1\n• point 2"
}"""

        user_prompt = f"""Health Claim: "{claim}"

Studies to Analyze:
{studies_context}

Analyze these studies and generate a verdict about the health claim."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await invoke_with_retry(self.llm, messages)

            # Parse JSON response
            import json
            import re

            content = response.content

            # Extract JSON from markdown code blocks
            content = re.sub(r"```(?:json)?\s*|\s*```", "", content).strip()

            # strict=False allows literal control chars (newlines, tabs)
            # inside strings — LLMs emit these regularly in bullet-point fields
            result = json.loads(content, strict=False)

            # Assemble structured fields into a markdown summary
            sections = []
            sections.append(
                f"## Bottom Line\n{result.get('bottom_line', 'No summary available.')}"
            )
            sections.append(
                f"## What Research Found\n{result.get('what_research_found', '')}"
            )
            sections.append(
                f"## Who Benefits Most\n{result.get('who_benefits_most', '')}"
            )
            if result.get("dosage_and_timing"):
                sections.append(f"## Dosage & Timing\n{result['dosage_and_timing']}")
            sections.append(
                f"## Important Caveats\n{result.get('important_caveats', '')}"
            )

            summary = "\n\n".join(sections)

            return {
                "verdict": result.get("verdict", "Inconclusive"),
                "verdict_emoji": result.get("verdict_emoji", "❓"),
                "summary": summary,
            }

        except Exception as e:
            print(f"❌ Synthesis failed: {e}")
            # Fallback response
            return {
                "verdict": "Inconclusive",
                "verdict_emoji": "❓",
                "summary": "Unable to synthesize evidence. Please try again later.",
            }

    async def run(self, state: VerityState) -> VerityState:
        """Execute Synthesis Agent node in LangGraph workflow.

        Args:
            state: Current graph state with 'top_studies' field

        Returns:
            Updated state with verdict, verdict_emoji, and summary added
        """
        claim = state.get("claim", "")
        top_studies = state.get("top_studies", [])

        if not top_studies:
            print("⚠️  No studies to synthesize")
            return {
                **state,
                "verdict": "Inconclusive",
                "verdict_emoji": "❓",
                "summary": "No quality studies found to evaluate this claim.",
            }

        try:
            print(f"\n🔬 Synthesis Agent: Analyzing {len(top_studies)} top studies...")

            # Generate verdict and summary
            result = await self.synthesize_verdict(claim, top_studies)

            # Display results
            print(f"\n{'=' * 80}")
            print(f"📊 FINAL VERDICT: {result['verdict_emoji']} {result['verdict']}")
            print(f"{'=' * 80}")
            print(f"\n{result['summary']}")

            print(f"\n{'=' * 80}")

            # Return updated state
            return {
                **state,
                "verdict": result["verdict"],
                "verdict_emoji": result["verdict_emoji"],
                "summary": result["summary"],
            }

        except Exception as e:
            print(f"❌ Synthesis Agent failed: {e}")
            return {
                **state,
                "verdict": "Inconclusive",
                "verdict_emoji": "❓",
                "summary": "Unable to synthesize evidence. Please try again later.",
            }


# Node function for LangGraph
async def synthesis_node(state: VerityState) -> VerityState:
    """LangGraph node wrapper for Synthesis Agent.

    This function is called by LangGraph during workflow execution.
    """
    agent = SynthesisAgent()
    return await agent.run(state)
