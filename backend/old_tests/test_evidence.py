from app.agents.search_agent import search_agent
from app.intelligence.evidence import evidence_engine

sources = search_agent.search(
    ["LangGraph"]
)

paragraph = """
LangGraph provides orchestration
for AI agents.
"""

result = evidence_engine.verify(
    paragraph,
    sources,
)

print(result.model_dump())