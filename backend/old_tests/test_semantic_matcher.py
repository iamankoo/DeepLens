from app.agents.search_agent import search_agent
from app.search.semantic_matcher import semantic_matcher

print("Searching...")

sources = search_agent.search(["LangGraph"])

print("Sources:", len(sources))

paragraph = """
LangGraph provides orchestration
for stateful AI agents.
"""

print("Matching...")

best = semantic_matcher.best_match(
    paragraph,
    sources,
)

print("Done")

print("\nBest Match")
print("=" * 40)

print("Source :", best.source)
print("Title  :", best.title)
print("Score  :", best.credibility_score)
print("URL    :", best.url)