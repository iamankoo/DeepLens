from app.agents.search_agent import search_agent
from app.citations.extractor import citation_extractor
from pprint import pprint

queries = [
    "LangGraph"
]

results = search_agent.search(
    queries
)

citations = citation_extractor.extract(
    results
)

from pprint import pprint

pprint(
    citations.model_dump(),
    sort_dicts=False,
)