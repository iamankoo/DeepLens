from collections.abc import Callable

from app.core.logger import logger
from app.workflows.workflow_manager import workflow_manager


class ResearchAgent:

    def run(self, query: str, on_step: Callable[[str], None] | None = None):

        logger.debug("research agent started")

        result = workflow_manager.run(query, on_step=on_step)

        logger.debug("research agent finished")

        return result


research_agent = ResearchAgent()
