from app.rewrite.planner import rewrite_planner
from app.rewrite.agent import rewrite_agent
from app.rewrite.manager import rewrite_manager
from app.intelligence.quality import quality_engine
from app.search.schemas import SearchResult


def test_rewrite():

    print("Testing Rewrite Engine...")

    sources = [
        SearchResult(
            title="LangGraph Overview",
            url="https://www.ibm.com/think/topics/langgraph",
            snippet="LangGraph is an open source AI agent orchestration framework created by LangChain."
        )
    ]

    report = "LangGraph is an orchestration framework.\n\nLangGraph was invented in 1952 by Julius Caesar."

    quality = quality_engine.evaluate(report, sources)

    tasks = rewrite_planner.create_plan(quality)

    assert len(tasks) > 0, "No rewrite tasks planned for false claim"

    assert tasks[0].claims != [], "Claims list is empty"

    response = rewrite_agent.rewrite(tasks[0])

    assert response.rewritten_paragraph != "", "Rewrite agent returned empty paragraph"

    assert "Julius Caesar" not in response.rewritten_paragraph, "Failed to remove false claim"

    improved = rewrite_manager.improve_report(report, sources)

    assert "Julius Caesar" not in improved, "Manager failed to replace unsupported paragraph"

    print("Rewrite Engine works successfully.")


if __name__ == "__main__":

    test_rewrite()
