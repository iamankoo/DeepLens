from app.agents.search_agent import search_agent
from app.intelligence.quality import quality_engine
from app.rewrite.planner import rewrite_planner

sources = search_agent.search(["LangGraph"])

report = """
LangGraph is a framework.

LangGraph can teleport data between planets.

LangGraph was invented in 1952.
"""

quality = quality_engine.evaluate(
    report,
    sources,
)

tasks = rewrite_planner.create_plan(
    quality,
)

for task in tasks:
    print(task.model_dump())