import re


class ClaimExtractor:

    def extract(
        self,
        paragraph: str,
    ) -> list[str]:

        paragraph = paragraph.strip()

        if not paragraph:
            return []

        claims = re.split(
            r"(?<=[.!?])\s+",
            paragraph,
        )

        return [
            claim.strip()
            for claim in claims
            if claim.strip()
        ]


claim_extractor = ClaimExtractor()