import time

from pydantic import BaseModel

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
        print(f"    [SemanticMatcher] Matching paragraph against {total} sources "
              f"(capped from {len(sources)})...")

        t0_total = time.perf_counter()

        for i, source in enumerate(capped_sources, 1):

            print(f"    [SemanticMatcher] Source {i}/{total}: {source.url[:80]}")
            t0 = time.perf_counter()

            try:
                chunks = retrieval_manager.retrieve(
                    query=paragraph,
                    title=source.title,
                    url=source.url,
                    top_k=1,
                )
            except Exception as e:
                print(f"    [SemanticMatcher] ERROR retrieving from source {i}: {e}")
                continue

            elapsed = time.perf_counter() - t0

            if not chunks:
                print(f"    [SemanticMatcher] No chunks returned ({elapsed:.2f}s)")
                continue

            chunk = chunks[0]
            print(f"    [SemanticMatcher] Score={chunk.similarity:.4f} ({elapsed:.2f}s)")

            if chunk.similarity > best_score:
                best_score = chunk.similarity
                best_chunk = chunk

        elapsed_total = time.perf_counter() - t0_total
        print(f"    [SemanticMatcher] Best score={best_score:.4f} in {elapsed_total:.2f}s total")

        return SemanticMatch(
            similarity_score=best_score,
            chunk=best_chunk,
        )


semantic_matcher = SemanticMatcher()