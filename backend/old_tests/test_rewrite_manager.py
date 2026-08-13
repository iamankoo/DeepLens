from app.agents.search_agent import search_agent
from app.rewrite.manager import rewrite_manager

sources = search_agent.search(
    ["LangGraph"]
)

report = """
LangGraph is a framework.

LangGraph can teleport data between planets.

LangGraph was invented in 1952.

LangGraph provides orchestration for AI workflows.
"""

improved = rewrite_manager.improve_report(
    report,
    sources,
)

print(improved)