from app.citations.extractor import citation_extractor
from app.citations.injector import citation_injector
from app.search.schemas import SearchResult


def test_citations():

    print("Testing Citation Extractor and Injector...")

    sources = [
        SearchResult(
            title="LangGraph Overview",
            url="https://www.ibm.com/think/topics/langgraph",
            snippet="LangGraph is an open source AI agent orchestration framework created by LangChain.",
            source="IBM",
            published_date="2024"
        )
    ]

    citations = citation_extractor.extract(sources)

    assert len(citations.citations) == 1, "Citation extraction failed"

    assert citations.citations[0].source == "IBM", "Source mismatch"

    report = "LangGraph is an orchestration framework."

    injected = citation_injector.inject(report, sources)

    assert "(IBM, 2024)" in injected, "Failed to inject citation"

    print("Citations system works successfully.")


if __name__ == "__main__":

    test_citations()
