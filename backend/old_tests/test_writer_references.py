from app.agents.writer_agent import writer_agent
from app.schemas.writer import WriterRequest
from app.search.schemas import SearchResult


request = WriterRequest(
    objective="Research LangGraph",
    tasks=[
        "Understand LangGraph",
        "Study Architecture",
        "Study Use Cases",
    ],
    sources=[
        SearchResult(
            title="What is LangGraph?",
            url="https://www.ibm.com/think/topics/langgraph",
            snippet="LangGraph is a framework for building stateful AI agents.",
            source="IBM",
            domain="ibm.com",
            credibility_score=90,
        ),
        SearchResult(
            title="LangGraph",
            url="https://www.langchain.com/langgraph",
            snippet="LangGraph provides orchestration for AI agents.",
            source="LangChain",
            domain="langchain.com",
            credibility_score=95,
        ),
    ],
)

response = writer_agent.generate_report(request)

print(response.report)