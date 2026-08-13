from app.agents.reflection_agent import reflection_agent
from app.schemas.reflection import ReflectionRequest

request = ReflectionRequest(
    objective="Research LangGraph",
    report="""
LangGraph is a framework for AI workflows.

It supports graphs and state management.
"""
)

response = reflection_agent.review(request)

print(response)