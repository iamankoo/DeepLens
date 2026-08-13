from app.agents.search_agent import search_agent
from app.intelligence.quality import quality_engine

sources = search_agent.search(["LangGraph"])

report = """
LangGraph is a framework for building stateful AI agents.

LangGraph provides orchestration for AI workflows.

LangGraph uses graphs to manage agent execution.

LangGraph was invented in 1952.

LangGraph can teleport data between planets.

LangGraph is maintained by the LangChain team.
"""

result = quality_engine.evaluate(
    report,
    sources,
)

print("\n")
print(result.model_dump())