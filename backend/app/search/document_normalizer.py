import re


class DocumentNormalizer:

    def normalize(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove spaces before punctuation
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)

        # Trim
        text = text.strip()

        return text


document_normalizer = DocumentNormalizer()