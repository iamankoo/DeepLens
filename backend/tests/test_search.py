from app.agents.search_agent import search_agent


def test_search():

    print("Testing Search Agent...")

    queries = ["LangGraph features"]

    results = search_agent.search(queries)

    assert len(results) > 0, "No search results found"

    assert results[0].url != "", "Empty URL in search results"

    print(f"Search works. Found {len(results)} results.")


if __name__ == "__main__":

    test_search()
