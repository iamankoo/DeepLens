from langgraph.graph import END, StateGraph

from app.workflows.nodes import (
    planner_node,
    search_node,
    ranking_node,
    writer_node,
    reflection_node,
    should_continue,
)
from app.workflows.state import ResearchState


workflow = StateGraph(ResearchState)

# -----------------------------
# Nodes
# -----------------------------

workflow.add_node("planner", planner_node)
workflow.add_node("search", search_node)
workflow.add_node("ranking", ranking_node)
workflow.add_node("writer", writer_node)
workflow.add_node("reflection", reflection_node)

# -----------------------------
# Entry Point
# -----------------------------

workflow.set_entry_point("planner")

# -----------------------------
# Normal Flow
# -----------------------------

workflow.add_edge("planner", "search")
workflow.add_edge("search", "ranking")
workflow.add_edge("ranking", "writer")
workflow.add_edge("writer", "reflection")

# -----------------------------
# Reflection Decision
# -----------------------------

workflow.add_conditional_edges(
    "reflection",
    should_continue,
    {
        "approve": END,
        "research_more": "search",
    },
)

# -----------------------------
# Compile
# -----------------------------

research_graph = workflow.compile()