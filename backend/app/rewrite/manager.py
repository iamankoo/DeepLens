import time

from app.intelligence.quality import quality_engine
from app.rewrite.agent import rewrite_agent
from app.rewrite.planner import rewrite_planner


class RewriteManager:

    def improve_report(
        self,
        report: str,
        sources,
    ) -> str:

        print("  [RewriteManager] Starting improve_report")
        t0 = time.perf_counter()

        print("  [RewriteManager] Evaluating quality...")
        quality_report = quality_engine.evaluate(
            report,
            sources,
        )

        print("  [RewriteManager] Planning rewrites...")
        tasks = rewrite_planner.create_plan(quality_report)

        if not tasks:
            print("  [RewriteManager] No rewrites needed — report is fully supported")
            return report

        paragraphs = [
            p.strip()
            for p in report.split("\n\n")
            if p.strip()
        ]

        total_tasks = len(tasks)
        for i, task in enumerate(tasks, 1):
            print(f"  [RewriteManager] Rewrite task {i}/{total_tasks} "
                  f"(paragraph {task.paragraph_index})")
            response = rewrite_agent.rewrite(task)
            paragraphs[response.paragraph_index] = response.rewritten_paragraph

        result = "\n\n".join(paragraphs)
        elapsed = time.perf_counter() - t0
        print(f"  [RewriteManager] improve_report done in {elapsed:.2f}s")
        return result


rewrite_manager = RewriteManager()