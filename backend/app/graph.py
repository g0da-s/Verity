"""LangGraph workflow orchestration for Verity.

This module defines the StateGraph that orchestrates the 3-agent pipeline:
Search Agent → Quality Evaluator → Synthesis Agent
"""

from langgraph.graph import StateGraph, END
from app.models.state import VerityState
from app.agents.search_agent import search_node
from app.agents.quality_evaluator import quality_evaluator_node
from app.agents.synthesis_agent import synthesis_node


workflow = StateGraph(VerityState)

workflow.add_node("search", search_node)
workflow.add_node("quality_evaluator", quality_evaluator_node)
workflow.add_node("synthesis", synthesis_node)

workflow.set_entry_point("search")
workflow.add_edge("search", "quality_evaluator")
workflow.add_edge("quality_evaluator", "synthesis")
workflow.add_edge("synthesis", END)

verity_graph = workflow.compile()


async def run_verity(claim: str) -> VerityState:
    """Run the Verity pipeline on a health claim.

    Args:
        claim: User's health claim to verify

    Returns:
        Final state with verdict, summary, and all intermediate results

    Example:
        >>> result = await run_verity("Does creatine improve muscle strength?")
        >>> print(f"{result['verdict_emoji']} {result['verdict']}")
        ✅ Strongly Supported
    """
    initial_state: VerityState = {"claim": claim}
    final_state = await verity_graph.ainvoke(initial_state)
    return final_state
