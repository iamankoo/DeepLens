from app.workflows.nodes import (
    planner_node,
    ranking_node,
    search_node,
    writer_node,
)
from app.workflows.state import ResearchState
from langgraph.graph import END, StateGraph

workflow = StateGraph(ResearchState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("search", search_node)
workflow.add_node("ranking", ranking_node)
workflow.add_node("writer", writer_node)

# Entry Point
workflow.set_entry_point("planner")

# Workflow
workflow.add_edge("planner", "search")
workflow.add_edge("search", "ranking")
workflow.add_edge("ranking", "writer")
workflow.add_edge("ranking", END)

# Compile
research_graph = workflow.compile()
