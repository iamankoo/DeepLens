from app.workflows.workflow_manager import workflow_manager
from app.core.logger import logger


class ResearchAgent:

    def run(self, query: str):

        logger.debug("research agent started")

        result = workflow_manager.run(query)

        logger.debug("research agent finished")

        return result


research_agent = ResearchAgent()
