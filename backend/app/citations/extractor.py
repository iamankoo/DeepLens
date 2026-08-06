from app.citations.schemas import Citation, CitationList


class CitationExtractor:

    def extract(self, search_results) -> CitationList:

        citations = []

        for result in search_results:

            citations.append(
                Citation(
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    source=result.get("source", ""),
                    author=result.get("author"),
                    published_date=result.get("published_date"),
                )
            )

        return CitationList(citations=citations)


citation_extractor = CitationExtractor()