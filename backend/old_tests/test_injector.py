from app.agents.search_agent import search_agent
from app.citations.injector import citation_injector

report = """
LangGraph is a framework for building stateful AI agents.

It provides orchestration for complex workflows.

LangGraph supports persistent memory.
"""

sources = search_agent.search(
    ["LangGraph"]
)

result = citation_injector.inject(
    report,
    sources,
)

print(result)