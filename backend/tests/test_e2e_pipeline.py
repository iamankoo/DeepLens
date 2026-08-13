from app.agents.research_agent import research_agent


def test_e2e_pipeline():

    print("Testing DeepLens End-to-End Research Pipeline...")

    query = "Research LangGraph core features and use cases"

    result = research_agent.run(query)

    assert "query" in result

    assert "report" in result

    assert result["report"] != ""

    assert "References" in result["report"]

    assert result["iteration"] >= 1

    assert "quality_report" in result

    assert result["quality_report"] is not None

    print("\n" + "=" * 80)

    print("E2E SUCCESS! FINAL REPORT GENERATED:")

    print("=" * 80)

    print(result["report"][:800] + "...\n[TRUNCATED]")

    print("=" * 80)

    print(f"Overall Quality Score: {result['quality_report'].overall_score}")

    print(f"Total Iterations: {result['iteration']}")

    print("=" * 80)


if __name__ == "__main__":

    test_e2e_pipeline()
