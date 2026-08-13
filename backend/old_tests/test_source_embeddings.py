from app.agents.search_agent import search_agent

results = search_agent.search(
    ["LangGraph"]
)

for result in results:

    print(result.source)

    print(len(result.embedding))