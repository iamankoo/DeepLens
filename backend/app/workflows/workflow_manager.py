from app.workflows.research_workflow import research_graph
from app.core.logger import logger


class WorkflowManager:

    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations

    def run(self, query: str) -> dict:

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

            result = research_graph.invoke(initial_state)

            logger.info(
                "state graph finished",
                extra={"iterations": result.get("iteration"), "report_chars": len(result.get("report", ""))},
            )

            return result

        except Exception:

            logger.exception("state graph execution failed")
            raise


workflow_manager = WorkflowManager()