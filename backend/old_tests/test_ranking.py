from app.agents.search_agent import search_agent
from app.agents.source_ranker import source_ranker

results = search_agent.search(["LangGraph"])

ranked = source_ranker.rank(results)

for source in ranked:
    print(
        source.credibility_score,
        source.source,
        source.title,
    )