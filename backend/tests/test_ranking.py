from app.agents.search_agent import search_agent
from app.agents.source_ranker import source_ranker


def test_ranking():

    print("Testing Source Ranker...")

    sources = search_agent.search(["LangGraph"])

    assert len(sources) > 0, "No sources found to rank"

    ranked = source_ranker.rank(sources)

    assert len(ranked) > 0, "No sources ranked"

    assert ranked[0].credibility_score >= 0, "Invalid credibility score"

    print(f"Ranking works. Ranked {len(ranked)} sources.")


if __name__ == "__main__":

    test_ranking()
