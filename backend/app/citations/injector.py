import time

import numpy as np

from app.core.logger import logger
from app.search.chunk import SearchChunk
from app.search.schemas import SearchResult
from app.memory.providers.sentence_transformer_provider import (
    sentence_transformer_provider,
)


class CitationInjector:
    """
    Injects inline APA citations into every paragraph.

    Uses BATCH embedding for all paragraphs at once — no per-paragraph
    model call overhead.
    """

    def inject(
        self,
        report: str,
        sources: list[SearchResult],
        chunk_pool: list[SearchChunk] | None = None,
    ) -> str:

        paragraphs = [
            p.strip()
            for p in report.split("\n\n")
            if p.strip()
        ]

        total = len(paragraphs)
        pool_size = len(chunk_pool) if chunk_pool else 0
        logger.debug(
            "injecting citations",
            extra={"paragraphs": total, "chunk_pool": pool_size, "sources": len(sources)},
        )

        # Build URL -> source lookup
        url_to_source: dict[str, SearchResult] = {
            src.url.strip().lower(): src for src in sources
        }

        if chunk_pool:
            updated = self._inject_from_pool(paragraphs, chunk_pool, url_to_source)
        else:
            updated = self._inject_from_sources(paragraphs, sources)

        result = "\n\n".join(updated)
        logger.debug("citation injection done", extra={"paragraphs": total})
        return result

    # ── Fast batch pool path ──────────────────────────────────────────────────

    def _inject_from_pool(
        self,
        paragraphs: list[str],
        chunk_pool: list[SearchChunk],
        url_to_source: dict[str, SearchResult],
    ) -> list[str]:

        # Filter chunks that have embeddings
        valid_chunks = [c for c in chunk_pool if c.embedding is not None]
        logger.debug("valid embedded chunks", extra={"count": len(valid_chunks)})

        if not valid_chunks:
            logger.warning("no valid chunks — no citations injected")
            return paragraphs

        # Stack chunk embeddings into matrix
        try:
            chunk_matrix = np.array([c.embedding for c in valid_chunks])  # (N, D)
        except Exception as e:
            logger.error("error building chunk matrix", extra={"error": str(e)})
            return paragraphs

        # Batch embed ALL paragraphs in one forward pass
        t0 = time.perf_counter()
        try:
            para_matrix = np.array(
                sentence_transformer_provider.model.encode(
                    paragraphs,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    batch_size=32,
                )
            )  # (P, D)
        except Exception as e:
            logger.error("error batch-embedding paragraphs", extra={"error": str(e)})
            return paragraphs

        elapsed = time.perf_counter() - t0
        logger.debug(
            "batch embedded paragraphs",
            extra={"paragraph_count": len(paragraphs), "elapsed_s": round(elapsed, 2)},
        )

        # (P, N) scores matrix
        scores_matrix = para_matrix @ chunk_matrix.T

        updated = []
        for i, (paragraph, scores) in enumerate(zip(paragraphs, scores_matrix), 1):
            best_idx = int(np.argmax(scores))
            best_score = float(scores[best_idx])
            best_chunk = valid_chunks[best_idx]

            if best_score <= 0:
                logger.debug("no match for paragraph — no citation", extra={"paragraph_index": i, "score": round(best_score, 4)})
                updated.append(paragraph)
                continue

            url_key = best_chunk.source_url.strip().lower()
            matching_source = url_to_source.get(url_key)

            if matching_source:
                source_name = matching_source.source or best_chunk.source_name or "Unknown"
                published_date = matching_source.published_date or "n.d."
            else:
                source_name = best_chunk.source_name or "Unknown"
                published_date = "n.d."

            citation = f" ({source_name}, {published_date})"
            logger.debug(
                "citation matched",
                extra={"paragraph_index": i, "source_name": source_name, "score": round(best_score, 4)},
            )
            updated.append(paragraph + citation)

        return updated

    # ── Slow legacy path ──────────────────────────────────────────────────────

    def _inject_from_sources(
        self,
        paragraphs: list[str],
        sources: list[SearchResult],
    ) -> list[str]:
        try:
            from app.search.semantic_matcher import semantic_matcher
        except Exception:
            return paragraphs

        updated = []
        for i, paragraph in enumerate(paragraphs, 1):
            logger.debug("citation injection (slow path)", extra={"paragraph_index": i, "total": len(paragraphs)})
            try:
                match = semantic_matcher.best_match(paragraph, sources)
                if match.chunk and match.similarity_score > 0:
                    src = next(
                        (s for s in sources if s.url.strip().lower() == match.chunk.source_url.strip().lower()),
                        None,
                    )
                    name = src.source if src else "Unknown"
                    date = src.published_date if src else "n.d."
                    updated.append(paragraph + f" ({name}, {date})")
                else:
                    updated.append(paragraph)
            except Exception as e:
                logger.error("citation injection error", extra={"paragraph_index": i, "error": str(e)})
                updated.append(paragraph)
        return updated


citation_injector = CitationInjector()