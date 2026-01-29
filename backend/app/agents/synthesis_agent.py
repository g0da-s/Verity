"""Synthesis Agent - Generates final verdict and evidence-based summary.

This agent:
1. Takes top-quality studies from Quality Evaluator
2. Analyzes study findings and abstracts
3. Generates verdict: Supported/Not Supported/Inconclusive
4. Creates evidence-based summary with citations

Final step in the TruthCheck pipeline.
"""

from typing import List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.models.state import TruthCheckState, Study


class SynthesisAgent:
    """Agent responsible for generating final verdict and summary.

    Uses Claude to analyze study findings and synthesize evidence-based
    conclusions about health claims.
    """

    def __init__(self):
        """Initialize Synthesis Agent with Claude Sonnet 4.5."""
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            api_key=settings.anthropic_api_key,
            temperature=0.2  # Low temp for factual synthesis
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
            score = study.get('quality_score', 0)
            context = f"""
Study {i} [Quality: {score:.1f}/10]:
- Title: {study.get('title', 'N/A')}
- Authors: {study.get('authors', 'N/A')}
- Journal: {study.get('journal', 'N/A')} ({study.get('year', 'N/A')})
- Study Type: {study.get('study_type', 'N/A')}
- Sample Size: n={study.get('sample_size', 0)}
- Abstract: {study.get('abstract', 'N/A')[:500]}...
- URL: {study.get('url', 'N/A')}
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

        system_prompt = """You are a scientific evidence synthesizer. Analyze the provided studies and generate an evidence-based verdict about a health claim.

VERDICT OPTIONS:
1. "Strongly Supported" - Multiple high-quality studies (meta-analyses/RCTs) show consistent positive evidence
2. "Supported" - Good quality studies show positive evidence with some consistency
3. "Partially Supported" - Mixed evidence, or limited scope of support
4. "Inconclusive" - Insufficient evidence, conflicting results, or low-quality studies
5. "Not Supported" - Quality studies show no benefit or refute the claim
6. "Contradicted" - Strong evidence actively contradicts the claim

EMOJI MAPPING:
- Strongly Supported: ✅
- Supported: ✓
- Partially Supported: ⚖️
- Inconclusive: ❓
- Not Supported: ❌
- Contradicted: 🚫

SUMMARY REQUIREMENTS:
1. Start with the verdict in one clear sentence
2. Cite specific studies with [Author, Year] format
3. Mention key findings (effect sizes, sample sizes, study quality)
4. Note any limitations or caveats
5. Keep it factual and evidence-based (no speculation)
6. Length: 3-5 paragraphs

IMPORTANT:
- Only use information from the provided studies
- Ignore any off-topic or irrelevant studies
- If studies are off-topic, mark as "Inconclusive - insufficient relevant evidence"
- Always cite specific studies for claims

OUTPUT FORMAT (JSON):
{
  "verdict": "verdict category here",
  "verdict_emoji": "emoji here",
  "summary": "Evidence-based summary here...",
  "key_findings": ["finding 1", "finding 2", "finding 3"]
}"""

        user_prompt = f"""Health Claim: "{claim}"

Studies to Analyze:
{studies_context}

Analyze these studies and generate a verdict about the health claim."""

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

            # Extract JSON from markdown code blocks
            content = re.sub(r'```(?:json)?\s*|\s*```', '', content).strip()

            result = json.loads(content)

            return {
                "verdict": result.get("verdict", "Inconclusive"),
                "verdict_emoji": result.get("verdict_emoji", "❓"),
                "summary": result.get("summary", "Unable to generate summary."),
                "key_findings": result.get("key_findings", [])
            }

        except Exception as e:
            print(f"❌ Synthesis failed: {e}")
            # Fallback response
            return {
                "verdict": "Inconclusive",
                "verdict_emoji": "❓",
                "summary": f"Unable to synthesize evidence due to error: {str(e)}",
                "key_findings": []
            }

    async def run(self, state: TruthCheckState) -> TruthCheckState:
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
                "summary": "No quality studies found to evaluate this claim."
            }

        try:
            print(f"\n🔬 Synthesis Agent: Analyzing {len(top_studies)} top studies...")

            # Generate verdict and summary
            result = await self.synthesize_verdict(claim, top_studies)

            # Display results
            print(f"\n{'='*80}")
            print(f"📊 FINAL VERDICT: {result['verdict_emoji']} {result['verdict']}")
            print(f"{'='*80}")
            print(f"\n{result['summary']}")

            if result.get('key_findings'):
                print(f"\n{'='*80}")
                print("🔑 Key Findings:")
                for i, finding in enumerate(result['key_findings'], 1):
                    print(f"   {i}. {finding}")

            print(f"\n{'='*80}")

            # Return updated state
            return {
                **state,
                "verdict": result["verdict"],
                "verdict_emoji": result["verdict_emoji"],
                "summary": result["summary"]
            }

        except Exception as e:
            print(f"❌ Synthesis Agent failed: {e}")
            return {
                **state,
                "verdict": "Inconclusive",
                "verdict_emoji": "❓",
                "summary": f"Unable to synthesize evidence: {str(e)}"
            }


# Node function for LangGraph
async def synthesis_node(state: TruthCheckState) -> TruthCheckState:
    """LangGraph node wrapper for Synthesis Agent.

    This function is called by LangGraph during workflow execution.
    """
    agent = SynthesisAgent()
    return await agent.run(state)
