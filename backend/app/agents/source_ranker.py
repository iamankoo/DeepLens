class SourceRanker:

    def rank(self, sources: list[dict]):

        seen_urls = set()
        seen_titles = set()

        ranked = []

        for source in sources:

            url = source["url"].strip().lower()
            title = source["title"].strip().lower().replace("?", "").replace("...", "")

            if url in seen_urls:
                continue

            if title in seen_titles:
                continue

            seen_urls.add(url)
            seen_titles.add(title)

            ranked.append(source)

        return ranked


source_ranker = SourceRanker()
