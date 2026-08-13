import time

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

        print(f"  [QualityEngine] Evaluating {total_paragraphs} paragraphs "
              f"| chunk_pool={pool_size} | sources={src_count}")

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
            print(f"  [QualityEngine] Para {i}/{total}: "
                  f"level={r.evidence_level.value} "
                  f"score={r.similarity_score:.4f} "
                  f"supported={r.supported}")

        evidence_score = (supported / total if total else 0) * 100
        hallucination_score = (hallucinated / total if total else 0) * 100
        overall_score = evidence_score * 0.7 + (100 - hallucination_score) * 0.3

        print(f"  [QualityEngine] Done in {elapsed:.2f}s — "
              f"overall={round(overall_score, 2)} supported={supported}/{total}")

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