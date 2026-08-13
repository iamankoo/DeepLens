from langgraph.graph import StateGraph, END

from app.workflows.state import ResearchState

from app.workflows.nodes import (
    planner_node,
    memory_search_node,
    search_node,
    ranking_node,
    chunking_node,
    retrieval_node,
    writer_node,
    verification_node,
    rewrite_node,
    citation_node,
    reflection_node,
    should_continue,
)

workflow = StateGraph(ResearchState)

# ------------------------------------------------------------------
# Nodes
# ------------------------------------------------------------------

workflow.add_node("planner", planner_node)
workflow.add_node("memory_search", memory_search_node)
workflow.add_node("search", search_node)
workflow.add_node("ranking", ranking_node)
workflow.add_node("chunking", chunking_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("writer", writer_node)
workflow.add_node("verification", verification_node)
workflow.add_node("rewrite", rewrite_node)
workflow.add_node("citation", citation_node)
workflow.add_node("reflection", reflection_node)

# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------

workflow.set_entry_point("planner")

# ------------------------------------------------------------------
# Main Pipeline
# ------------------------------------------------------------------

workflow.add_edge("planner", "memory_search")
workflow.add_edge("memory_search", "search")
workflow.add_edge("search", "ranking")
workflow.add_edge("ranking", "chunking")
workflow.add_edge("chunking", "retrieval")
workflow.add_edge("retrieval", "writer")
workflow.add_edge("writer", "verification")
workflow.add_edge("verification", "rewrite")
workflow.add_edge("rewrite", "citation")
workflow.add_edge("citation", "reflection")

# ------------------------------------------------------------------
# Reflection Loop
# ------------------------------------------------------------------

workflow.add_conditional_edges(
    "reflection",
    should_continue,
    {
        "approve": END,
        "research_more": "retrieval",
    },
)

research_graph = workflow.compile()