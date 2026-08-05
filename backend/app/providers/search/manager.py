from app.providers.search.tavily_provider import TavilyProvider


class SearchManager:

    def __init__(self):

        self.provider = TavilyProvider()

    def search(self, query: str):

        return self.provider.search(query)


search_manager = SearchManager()
