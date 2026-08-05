from app.providers.search.manager import search_manager


class SearchAgent:

    def generate_queries(self, objective: str):

        queries = list(
            dict.fromkeys(
                [
                    objective,
                    f"{objective} tutorial",
                    f"{objective} documentation",
                    f"{objective} examples",
                    f"{objective} best practices",
                ]
            )
        )

        return queries

    def search(self, queries: list[str]):

        all_results = []

        seen_urls = set()

        for query in queries:

            results = search_manager.search(query)

            for result in results:

                url = result["url"].strip().lower()

                if url in seen_urls:
                    continue

                seen_urls.add(url)
                all_results.append(result)

        return all_results


search_agent = SearchAgent()
