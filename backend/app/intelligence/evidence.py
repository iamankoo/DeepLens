import time

import numpy as np

from app.intelligence.evidence_level import EvidenceLevel
from app.intelligence.schemas import EvidenceResult
from app.search.chunk import SearchChunk
from app.memory.providers.sentence_transformer_provider import (
    sentence_transformer_provider,
)


class EvidenceEngine:
    """
    Verifies paragraphs against a pre-embedded chunk pool.

    Uses BATCH embedding for all paragraphs at once — no per-paragraph
    model call overhead.
    """

    STRONG_THRESHOLD = 7.0
    MODERATE_THRESHOLD = 4.5
    WEAK_THRESHOLD = 2.5

    def verify(
        self,
        paragraph: str,
        sources=None,
        chunk_pool: list[SearchChunk] | None = None,
    ) -> EvidenceResult:
        """Single-paragraph verify. Delegates to batch path."""
        results = self.verify_batch(
            paragraphs=[paragraph],
            chunk_pool=chunk_pool,
            sources=sources,
        )
        return results[0]

    def verify_batch(
        self,
        paragraphs: list[str],
        chunk_pool: list[SearchChunk] | None = None,
        sources=None,
    ) -> list[EvidenceResult]:
        """
        Batch verify all paragraphs at once.
        Single model.encode() call for all paragraph embeddings.
        """
        if not paragraphs:
            return []

        if chunk_pool:
            return self._batch_from_pool(paragraphs, chunk_pool)

        # Slow legacy path — one at a time
        print(f"    [EvidenceEngine] WARNING: no chunk_pool — slow path for {len(paragraphs)} paragraphs")
        return [self._verify_from_sources(p, sources or []) for p in paragraphs]

    # ── Batch fast path ───────────────────────────────────────────────────────

    def _batch_from_pool(
        self,
        paragraphs: list[str],
        chunk_pool: list[SearchChunk],
    ) -> list[EvidenceResult]:

        # Filter chunks with valid embeddings
        valid_chunks = [c for c in chunk_pool if c.embedding is not None]
        if not valid_chunks:
            print(f"    [EvidenceEngine] No valid embedded chunks -> all NONE")
            return [self._none_result(p) for p in paragraphs]

        # Stack chunk embeddings into matrix once
        try:
            chunk_matrix = np.array([c.embedding for c in valid_chunks])  # (N, D)
        except Exception as e:
            print(f"    [EvidenceEngine] ERROR building chunk matrix: {e}")
            return [self._none_result(p) for p in paragraphs]

        # Batch embed all paragraphs in ONE model call
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
            print(f"    [EvidenceEngine] ERROR batch-embedding paragraphs: {e}")
            return [self._none_result(p) for p in paragraphs]

        elapsed = time.perf_counter() - t0
        print(f"    [EvidenceEngine] Batch embedded {len(paragraphs)} paragraphs in {elapsed:.2f}s")

        # Dot product: (P, D) @ (D, N) = (P, N)
        scores_matrix = para_matrix @ chunk_matrix.T  # (P, N)

        results = []
        for i, (paragraph, scores) in enumerate(zip(paragraphs, scores_matrix)):
            best_idx = int(np.argmax(scores))
            best_score = float(scores[best_idx])
            best_chunk = valid_chunks[best_idx]

            level = self._classify(best_score)
            supported = level != EvidenceLevel.NONE
            hallucination = not supported

            # Return copy with embedding stripped
            safe_chunk = best_chunk.model_copy(update={"embedding": None})

            results.append(EvidenceResult(
                paragraph=paragraph,
                evidence_level=level,
                supported=supported,
                hallucination=hallucination,
                similarity_score=round(best_score, 4),
                confidence=round(best_score, 4),
                best_chunk=safe_chunk,
            ))

        return results

    # ── Legacy slow path ──────────────────────────────────────────────────────

    def _verify_from_sources(self, paragraph: str, sources: list) -> EvidenceResult:
        try:
            from app.search.semantic_matcher import semantic_matcher
            match = semantic_matcher.best_match(paragraph, sources)
            if match.chunk is None:
                return self._none_result(paragraph)
            score = match.similarity_score
            level = self._classify(score)
            supported = level != EvidenceLevel.NONE
            safe_chunk = match.chunk.model_copy(update={"embedding": None})
            return EvidenceResult(
                paragraph=paragraph,
                evidence_level=level,
                supported=supported,
                hallucination=not supported,
                similarity_score=round(score, 4),
                confidence=round(score, 4),
                best_chunk=safe_chunk,
            )
        except Exception as e:
            print(f"    [EvidenceEngine] semantic_matcher ERROR: {e}")
            return self._none_result(paragraph)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _classify(self, score: float) -> EvidenceLevel:
        if score <= 1.0:
            if score >= 0.60:
                return EvidenceLevel.STRONG
            if score >= 0.40:
                return EvidenceLevel.MODERATE
            if score >= 0.20:
                return EvidenceLevel.WEAK
            return EvidenceLevel.NONE
        else:
            if score >= self.STRONG_THRESHOLD:
                return EvidenceLevel.STRONG
            if score >= self.MODERATE_THRESHOLD:
                return EvidenceLevel.MODERATE
            if score >= self.WEAK_THRESHOLD:
                return EvidenceLevel.WEAK
            return EvidenceLevel.NONE

    def _none_result(self, paragraph: str) -> EvidenceResult:
        return EvidenceResult(
            paragraph=paragraph,
            evidence_level=EvidenceLevel.NONE,
            supported=False,
            hallucination=True,
            similarity_score=0.0,
            confidence=0.0,
            best_chunk=None,
        )


evidence_engine = EvidenceEngine()