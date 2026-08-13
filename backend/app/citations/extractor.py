from app.citations.schemas import Citation, CitationList
from app.search.schemas import SearchResult


class CitationExtractor:

    def extract(
        self,
        search_results: list[SearchResult],
    ) -> CitationList:

        citations = []

        for result in search_results:

            citations.append(
                Citation(
                    title=result.title,
                    url=result.url,
                    source=result.source,
                    domain=result.domain,
                    author=result.author,
                    publisher=result.source,
                    published_date=result.published_date,
                    credibility_score=result.credibility_score,
                )
            )

        return CitationList(
            citations=citations
        )


citation_extractor = CitationExtractor()