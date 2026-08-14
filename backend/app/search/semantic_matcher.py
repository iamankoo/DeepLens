import time

from pydantic import BaseModel

from app.core.logger import logger
from app.search.chunk import SearchChunk
from app.search.retrieval_manager import retrieval_manager
from app.search.schemas import SearchResult


class SemanticMatch(BaseModel):

    similarity_score: float

    chunk: SearchChunk | None = None


class SemanticMatcher:

    # Cap how many sources we download-and-chunk per paragraph during
    # verification/citation to avoid O(paragraphs × sources) hang.
    MAX_SOURCES_PER_MATCH = 5

    def best_match(
        self,
        paragraph: str,
        sources: list[SearchResult],
    ) -> SemanticMatch:

        if not sources:
            return SemanticMatch(
                similarity_score=0.0,
                chunk=None,
            )

        # Only examine the top-N sources to keep verification fast
        capped_sources = sources[: self.MAX_SOURCES_PER_MATCH]

        best_chunk = None
        best_score = -1.0

        total = len(capped_sources)
        logger.debug(
            "matching paragraph against sources",
            extra={"total": total, "uncapped_total": len(sources)},
        )

        t0_total = time.perf_counter()

        for i, source in enumerate(capped_sources, 1):

            logger.debug("matching source", extra={"index": i, "total": total, "url": source.url[:80]})
            t0 = time.perf_counter()

            try:
                chunks = retrieval_manager.retrieve(
                    query=paragraph,
                    title=source.title,
                    url=source.url,
                    top_k=1,
                )
            except Exception as e:
                logger.error("error retrieving from source", extra={"index": i, "error": str(e)})
                continue

            elapsed = time.perf_counter() - t0

            if not chunks:
                logger.debug("no chunks returned", extra={"elapsed_s": round(elapsed, 2)})
                continue

            chunk = chunks[0]
            logger.debug("source scored", extra={"score": round(chunk.similarity, 4), "elapsed_s": round(elapsed, 2)})

            if chunk.similarity > best_score:
                best_score = chunk.similarity
                best_chunk = chunk

        elapsed_total = time.perf_counter() - t0_total
        logger.debug(
            "best match found",
            extra={"best_score": round(best_score, 4), "elapsed_s": round(elapsed_total, 2)},
        )

        return SemanticMatch(
            similarity_score=best_score,
            chunk=best_chunk,
        )


semantic_matcher = SemanticMatcher()