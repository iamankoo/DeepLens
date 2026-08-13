from app.search.chunk import SearchChunk


class ChunkRanker:

    def rank(
        self,
        query: str,
        chunks: list[SearchChunk],
    ) -> list[SearchChunk]:

        query_words = {
            word.lower()
            for word in query.split()
        }

        for chunk in chunks:

            semantic = chunk.similarity

            text_words = {
                word.lower()
                for word in chunk.text.split()
            }

            keyword_score = (
                len(query_words & text_words)
                / max(len(query_words), 1)
            )

            position_score = max(
                0,
                1 - (chunk.chunk_id * 0.05),
            )

            chunk.similarity = (
                semantic * 0.75
                + keyword_score * 0.15
                + position_score * 0.10
            )

        chunks.sort(
            key=lambda c: c.similarity,
            reverse=True,
        )

        return chunks


chunk_ranker = ChunkRanker()