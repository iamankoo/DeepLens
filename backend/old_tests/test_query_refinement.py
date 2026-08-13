from app.agents.query_refinement_agent import query_refinement_agent
from app.schemas.query_refinement import QueryRefinementRequest


request = QueryRefinementRequest(
    objective="Research LangGraph",
    previous_queries=[
        "What is LangGraph?",
        "LangGraph architecture",
        "LangGraph tutorial",
    ],
    missing_information=[
        "Performance benchmarks",
        "Comparison with CrewAI",
        "Scalability",
    ],
)

response = query_refinement_agent.generate_queries(request)

print(response)