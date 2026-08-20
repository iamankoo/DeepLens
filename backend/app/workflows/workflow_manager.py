import time
from collections.abc import Callable

from app.core.config import settings
from app.core.exceptions import ResearchTimeoutError
from app.core.logger import logger
from app.workflows.research_workflow import research_graph


class WorkflowManager:

    def __init__(self, max_iterations: int | None = None):
        # Defaults from Settings.RESEARCH_MAX_ITERATIONS (see its docstring
        # in app/core/config.py) rather than a hardcoded 3 — the reflection
        # loop's iteration ceiling has to be chosen with the 120s time
        # budget in mind, not independently of it.
        self.max_iterations = max_iterations if max_iterations is not None else settings.RESEARCH_MAX_ITERATIONS

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

        start_time = time.monotonic()
        budget = settings.RESEARCH_TIME_BUDGET_SECONDS
        last_node = "planner"

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
                elif mode == "updates":
                    for node_name in chunk:
                        last_node = node_name
                        if on_step:
                            on_step(node_name)

                # Cooperative time-budget check, run between every node
                # (including before the reflection loop is allowed to start
                # another retrieval -> writer -> ... iteration, its single
                # biggest source of unbounded total runtime). Deliberately
                # checked after both stream modes so a node that fires only
                # a "values" update on the final step is still covered.
                # This can only catch a run that's over budget AT a node
                # boundary — a single node blocking past the budget inside
                # one call is instead caught by the harder, OS-level
                # RQ job_timeout (see Settings.RESEARCH_JOB_TIMEOUT_SECONDS).
                elapsed = time.monotonic() - start_time
                if elapsed > budget:
                    logger.error(
                        "research exceeded time budget — stopping cooperatively",
                        extra={"elapsed_s": round(elapsed, 1), "budget_s": budget, "last_completed_node": last_node},
                    )
                    raise ResearchTimeoutError(
                        f"Research exceeded its {budget}s time budget after completing "
                        f"the '{last_node}' stage. Please try again with a narrower query."
                    )

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
