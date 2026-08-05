from app.agents.writer_agent import writer_agent
from app.schemas.writer import WriterRequest

request = WriterRequest(
    objective="Research LangGraph",
    tasks=[
        "Architecture",
        "State Management",
        "Use Cases"
    ],
    sources=[
        {
            "title": "LangGraph Docs",
            "url": "https://langchain-ai.github.io/langgraph/",
            "content": "LangGraph is..."
        }
    ]
)

response = writer_agent.generate_report(request)

print(response.report)