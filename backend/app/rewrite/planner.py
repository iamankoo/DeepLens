import time

from app.intelligence.evidence_level import EvidenceLevel
from app.intelligence.quality_schema import QualityReport
from app.rewrite.rewrite_strategy import RewriteStrategy
from app.rewrite.schemas import RewriteSource, RewriteTask
from app.rewrite.claim_extractor import claim_extractor


class RewritePlanner:

    def create_plan(
        self,
        quality_report: QualityReport,
    ) -> list[RewriteTask]:

        total = len(quality_report.evidence_results)
        print(f"  [RewritePlanner] Planning rewrites for {total} paragraphs")
        t0 = time.perf_counter()

        tasks = []

        for index, result in enumerate(quality_report.evidence_results):

            print(f"  [RewritePlanner] Paragraph {index+1}/{total}: "
                  f"level={result.evidence_level.value}")

            if result.evidence_level in (
                EvidenceLevel.STRONG,
                EvidenceLevel.MODERATE,
            ):
                print(f"  [RewritePlanner]   -> Skipping (well-supported)")
                continue

            strategy = (
                RewriteStrategy.IMPROVE
                if result.evidence_level == EvidenceLevel.WEAK
                else RewriteStrategy.REWRITE
            )

            source = None
            claims = claim_extractor.extract(result.paragraph)

            if result.best_chunk:
                source = RewriteSource(
                    title=result.best_chunk.source_title,
                    url=result.best_chunk.source_url,
                    snippet=result.best_chunk.text[:600],
                    source=result.best_chunk.source_name or "Unknown",
                )

            print(f"  [RewritePlanner]   -> strategy={strategy.value}, "
                  f"claims={len(claims)}, has_source={source is not None}")

            tasks.append(
                RewriteTask(
                    paragraph_index=index,
                    original_paragraph=result.paragraph,
                    claims=claims,
                    evidence_level=result.evidence_level,
                    rewrite_strategy=strategy,
                    source=source,
                )
            )

        # Cap rewrite tasks to avoid long sequential LLM calls
        MAX_REWRITE_TASKS = 3
        if len(tasks) > MAX_REWRITE_TASKS:
            print(f"  [RewritePlanner] Capping rewrite tasks from {len(tasks)} to {MAX_REWRITE_TASKS}")
            tasks = tasks[:MAX_REWRITE_TASKS]

        elapsed = time.perf_counter() - t0
        print(f"  [RewritePlanner] Done — {len(tasks)} rewrite tasks in {elapsed:.2f}s")
        return tasks


rewrite_planner = RewritePlanner()