from app.citations.reference_manager import reference_manager
from app.citations.schemas import Citation

citations = [
    Citation(
        title="What is LangGraph?",
        url="https://www.ibm.com/think/topics/langgraph",
        source="IBM",
    ),
    Citation(
        title="LangGraph",
        url="https://www.langchain.com/langgraph",
        source="LangChain",
    ),
]

print(
    reference_manager.generate(
        citations,
        style="APA",
    )
)