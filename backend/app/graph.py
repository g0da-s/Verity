"""LangGraph workflow orchestration for TruthCheck.

This module defines the StateGraph that orchestrates the 3-agent pipeline:
Search Agent → Quality Evaluator → Synthesis Agent
"""

from langgraph.graph import StateGraph, END
from app.models.state import TruthCheckState
from app.agents.search_agent import search_node
from app.agents.quality_evaluator import quality_evaluator_node
from app.agents.synthesis_agent import synthesis_node


# Initialize the graph with our state schema
workflow = StateGraph(TruthCheckState)

# Add the 3 agent nodes
workflow.add_node("search", search_node)
workflow.add_node("quality_evaluator", quality_evaluator_node)
workflow.add_node("synthesis", synthesis_node)

# Define the flow: search → quality → synthesis → END
workflow.set_entry_point("search")
workflow.add_edge("search", "quality_evaluator")
workflow.add_edge("quality_evaluator", "synthesis")
workflow.add_edge("synthesis", END)

# Compile the graph
truthcheck_graph = workflow.compile()


async def run_truthcheck(claim: str) -> TruthCheckState:
    """Run the TruthCheck pipeline on a health claim.

    Args:
        claim: User's health claim to verify

    Returns:
        Final state with verdict, summary, and all intermediate results

    Example:
        >>> result = await run_truthcheck("Does creatine improve muscle strength?")
        >>> print(f"{result['verdict_emoji']} {result['verdict']}")
        ✅ Strongly Supported
    """
    initial_state: TruthCheckState = {"claim": claim}
    final_state = await truthcheck_graph.ainvoke(initial_state)
    return final_state
