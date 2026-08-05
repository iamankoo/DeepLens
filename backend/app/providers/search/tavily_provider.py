from app.core.config import settings
from app.providers.search.base import BaseSearchProvider
from tavily import TavilyClient


class TavilyProvider(BaseSearchProvider):

    def __init__(self):

        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    def search(self, query: str):

        response = self.client.search(
            query=query,
            search_depth="basic",
            max_results=5,
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
