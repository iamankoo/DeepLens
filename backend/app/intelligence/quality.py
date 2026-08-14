import time

from app.core.logger import logger
from app.intelligence.evidence import evidence_engine
from app.intelligence.quality_schema import QualityReport
from app.search.schemas import SearchResult
from app.search.chunk import SearchChunk


class QualityEngine:
    """
    Evaluates evidence quality for every paragraph in a report.

    Uses evidence_engine.verify_batch() — one batch embedding call
    for ALL paragraphs, not one per paragraph.
    """

    def evaluate(
        self,
        report: str,
        sources: list[SearchResult] | None = None,
        chunk_pool: list[SearchChunk] | None = None,
    ) -> QualityReport:

        paragraphs = [
            p.strip()
            for p in report.split("\n\n")
            if p.strip()
        ]

        total_paragraphs = len(paragraphs)
        pool_size = len(chunk_pool) if chunk_pool else 0
        src_count = len(sources) if sources else 0

        logger.debug(
            "evaluating quality",
            extra={"total_paragraphs": total_paragraphs, "chunk_pool": pool_size, "sources": src_count},
        )

        t0 = time.perf_counter()

        # Single batch call — all paragraphs embedded in one forward pass
        evidence_results = evidence_engine.verify_batch(
            paragraphs=paragraphs,
            chunk_pool=chunk_pool,
            sources=sources,
        )

        total = len(evidence_results)
        supported = sum(r.supported for r in evidence_results)
        hallucinated = total - supported

        elapsed = time.perf_counter() - t0

        for i, r in enumerate(evidence_results, 1):
            logger.debug(
                "paragraph evidence evaluated",
                extra={
                    "index": i,
                    "total": total,
                    "evidence_level": r.evidence_level.value,
                    "score": round(r.similarity_score, 4),
                    "supported": r.supported,
                },
            )

        evidence_score = (supported / total if total else 0) * 100
        hallucination_score = (hallucinated / total if total else 0) * 100
        overall_score = evidence_score * 0.7 + (100 - hallucination_score) * 0.3

        logger.debug(
            "quality evaluation done",
            extra={
                "elapsed_s": round(elapsed, 2),
                "overall_score": round(overall_score, 2),
                "supported": supported,
                "total": total,
            },
        )

        return QualityReport(
            total_paragraphs=total,
            supported_paragraphs=supported,
            hallucinated_paragraphs=hallucinated,
            evidence_score=round(evidence_score, 2),
            hallucination_score=round(hallucination_score, 2),
            overall_score=round(overall_score, 2),
            evidence_results=evidence_results,
        )


quality_engine = QualityEngine()