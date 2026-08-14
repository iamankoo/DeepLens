import time

from app.core.logger import logger
from app.intelligence.quality import quality_engine
from app.rewrite.agent import rewrite_agent
from app.rewrite.planner import rewrite_planner


class RewriteManager:

    def improve_report(
        self,
        report: str,
        sources,
    ) -> str:

        logger.debug("starting improve_report")
        t0 = time.perf_counter()

        logger.debug("evaluating quality")
        quality_report = quality_engine.evaluate(
            report,
            sources,
        )

        logger.debug("planning rewrites")
        tasks = rewrite_planner.create_plan(quality_report)

        if not tasks:
            logger.debug("no rewrites needed — report is fully supported")
            return report

        paragraphs = [
            p.strip()
            for p in report.split("\n\n")
            if p.strip()
        ]

        total_tasks = len(tasks)
        for i, task in enumerate(tasks, 1):
            logger.debug(
                "running rewrite task",
                extra={"index": i, "total": total_tasks, "paragraph_index": task.paragraph_index},
            )
            response = rewrite_agent.rewrite(task)
            paragraphs[response.paragraph_index] = response.rewritten_paragraph

        result = "\n\n".join(paragraphs)
        elapsed = time.perf_counter() - t0
        logger.debug("improve_report done", extra={"elapsed_s": round(elapsed, 2)})
        return result


rewrite_manager = RewriteManager()