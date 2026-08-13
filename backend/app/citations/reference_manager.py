from app.citations.formatter import citation_formatter
from app.citations.schemas import Citation


class ReferenceManager:

    def generate(
        self,
        citations: list[Citation],
        style: str = "APA",
    ) -> str:

        references = []

        for index, citation in enumerate(citations, start=1):

            if style.upper() == "APA":
                references.append(
                    citation_formatter.apa(citation)
                )

            elif style.upper() == "IEEE":
                references.append(
                    citation_formatter.ieee(
                        citation,
                        index,
                    )
                )

            elif style.upper() == "MLA":
                references.append(
                    citation_formatter.mla(citation)
                )

        return "\n\n".join(references)


reference_manager = ReferenceManager()