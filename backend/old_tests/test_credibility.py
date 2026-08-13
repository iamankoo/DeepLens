from app.agents.search_agent import search_agent

results = search_agent.search(
    ["LangGraph"]
)

for result in results:

    print()

    print(result.source)

    print(result.domain)

    print(result.credibility_score)

    print(result.title)