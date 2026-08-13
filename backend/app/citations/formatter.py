from app.citations.schemas import Citation


class CitationFormatter:

    def apa(
        self,
        citation: Citation,
    ) -> str:

        author = citation.author or citation.source

        year = citation.published_date or "n.d."

        return (
            f"{author}. ({year}). "
            f"{citation.title}. "
            f"{citation.url}"
        )

    def ieee(
        self,
        citation: Citation,
        index: int,
    ) -> str:

        return (
            f"[{index}] {citation.source}, "
            f"\"{citation.title}\", "
            f"Available: {citation.url}"
        )

    def mla(
        self,
        citation: Citation,
    ) -> str:

        author = citation.author or citation.source

        return (
            f'{author}. "{citation.title}." '
            f"{citation.url}"
        )


citation_formatter = CitationFormatter()