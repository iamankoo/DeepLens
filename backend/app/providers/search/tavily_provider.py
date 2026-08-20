from tavily import TavilyClient

from app.core.config import settings
from app.providers.search.base import BaseSearchProvider


class TavilyProvider(BaseSearchProvider):

    def __init__(self):

        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    def search(self, query: str, timeout: float | None = None):

        # TavilyClient's own default (60s) is unbounded relative to the
        # research pipeline's 120s total budget — search_agent.search()
        # calls this up to 3 times sequentially, so an unbounded/slow
        # response here could alone exceed the whole run's time budget.
        response = self.client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            timeout=timeout if timeout is not None else settings.SEARCH_REQUEST_TIMEOUT_SECONDS,
        )

        results = []

        seen_urls = set()

        for item in response["results"]:

            title = item["title"].strip()
            url = item["url"].strip()
            snippet = item["content"].strip()

            # Skip invalid URLs
            if not url.startswith("http"):
                continue

            # Skip Tavily redirect URLs
            if "/goto?" in url:
                continue

            # Remove duplicate URLs
            if url.lower() in seen_urls:
                continue

            seen_urls.add(url.lower())

            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

        return results
