from app.agents.writer_agent import writer_agent
from app.schemas.writer import WriterRequest
from app.search.schemas import SearchResult


def test_writer():

    print("Testing Writer Agent with Context...")

    request = WriterRequest(
        objective="Analyze LangGraph memory mechanisms",
        tasks=["Explain stateful serialization", "Discuss windowed summarization"],
        sources=[
            SearchResult(
                title="LangGraph Memory docs",
                url="https://langchain.com/langgraph/memory",
                snippet="LangGraph supports memory using persistent state checkpoints."
            )
        ],
        context="## Section: Memory mechanisms\nSource: LangGraph Memory docs\nSnippet: LangGraph supports memory using persistent state checkpoints.\n"
    )

    response = writer_agent.generate_report(request)

    assert response.report != "", "Writer returned empty report"

    assert "References" in response.report, "References section not appended"

    print("Writer Agent works successfully.")


if __name__ == "__main__":

    test_writer()
