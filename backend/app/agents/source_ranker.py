from app.search.schemas import SearchResult


class SourceRanker:

    def rank(
        self,
        sources: list[SearchResult],
    ) -> list[SearchResult]:

        seen_urls = set()

        unique_sources = []

        for source in sources:

            url = source.url.strip().lower()

            if url in seen_urls:
                continue

            seen_urls.add(url)

            unique_sources.append(source)

        unique_sources.sort(
            key=lambda x: x.credibility_score,
            reverse=True,
        )

        return unique_sources


source_ranker = SourceRanker()