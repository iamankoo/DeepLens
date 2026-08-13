from app.search.chunk import SearchChunk
from app.search.sentence_segmenter import sentence_segmenter


class SemanticChunker:

    MAX_SENTENCES = 8

    OVERLAP = 2

    def chunk(
        self,
        text: str,
        title: str,
        url: str,
    ) -> list[SearchChunk]:

        sentences = sentence_segmenter.segment(text)

        chunks = []

        chunk_id = 0

        start = 0

        while start < len(sentences):

            end = min(
                start + self.MAX_SENTENCES,
                len(sentences),
            )

            chunk_text = " ".join(
                sentences[start:end]
            )

            chunks.append(
                SearchChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    start_sentence=start,
                    end_sentence=end - 1,
                    source_url=url,
                    source_title=title,
                )
            )

            chunk_id += 1

            if end == len(sentences):
                break

            start = end - self.OVERLAP

        return chunks


semantic_chunker = SemanticChunker()