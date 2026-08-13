from app.agents.search_agent import search_agent
from app.intelligence.quality import quality_engine
from app.rewrite.agent import rewrite_agent
from app.rewrite.planner import rewrite_planner

sources = search_agent.search(
    ["LangGraph"]
)

report = """
LangGraph can teleport data between planets.
"""

quality = quality_engine.evaluate(
    report,
    sources,
)

tasks = rewrite_planner.create_plan(
    quality,
)

response = rewrite_agent.rewrite(
    tasks[0]
)

print(response.rewritten_paragraph)