from collections.abc import Callable

from app.core.logger import logger
from app.workflows.research_workflow import research_graph


class WorkflowManager:

    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations

    def run(self, query: str, on_step: Callable[[str], None] | None = None) -> dict:

        logger.info("workflow initializing", extra={"query": query, "max_iterations": self.max_iterations})

        initial_state = {
            "query": query,
            "objective": "",
            "tasks": [],
            "search_queries": [],
            "search_results": [],
            "ranked_sources": [],
            "chunk_pool": [],
            "context": "",
            "report": "",
            "quality_report": None,
            "reflection": None,
            "iteration": 0,
            "max_iterations": self.max_iterations,
            "memory_results": [],
            "memory_enabled": True,
        }

        logger.info("state graph invoking")

        try:
            # stream_mode=["updates", "values"] gives both which node just
            # ran (for on_step progress reporting) and the fully-merged
            # state after each step (so the final "values" chunk is exactly
            # what graph.invoke() would have returned) — this is why a
            # plain invoke() call was replaced with streaming.
            final_state: dict | None = None
            for mode, chunk in research_graph.stream(initial_state, stream_mode=["updates", "values"]):
                if mode == "values":
                    final_state = chunk
                elif mode == "updates" and on_step:
                    for node_name in chunk:
                        on_step(node_name)

            result = final_state or {}

            logger.info(
                "state graph finished",
                extra={"iterations": result.get("iteration"), "report_chars": len(result.get("report", ""))},
            )

            return result

        except Exception:

            logger.exception("state graph execution failed")
            raise


workflow_manager = WorkflowManager()
