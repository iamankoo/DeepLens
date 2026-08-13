from app.intelligence.evidence import evidence_engine
from app.intelligence.quality import quality_engine
from app.search.schemas import SearchResult


def test_evidence():

    print("Testing Evidence Engine & Quality Engine...")

    sources = [
        SearchResult(
            title="LangGraph Overview",
            url="https://www.ibm.com/think/topics/langgraph",
            snippet="LangGraph is an open source AI agent orchestration framework created by LangChain."
        )
    ]

    paragraph = "LangGraph is a framework for AI orchestration created by LangChain."

    result = evidence_engine.verify(paragraph, sources)

    assert result.paragraph == paragraph, "Paragraph mismatch"

    assert result.supported is True or result.evidence_level.value != "none", "Verify failed to support claim"

    assert result.best_chunk is not None, "Best chunk is None"

    assert result.best_chunk.embedding is None, "Leaked embedding inside EvidenceResult!"

    report = "LangGraph is a framework for AI orchestration.\n\nLangGraph can teleport data to space."

    quality = quality_engine.evaluate(report, sources)

    assert quality.total_paragraphs == 2, "Paragraph counting mismatch"

    assert quality.overall_score >= 0.0, "Invalid overall score"

    print("Evidence & Quality Engines work successfully.")


if __name__ == "__main__":

    test_evidence()
