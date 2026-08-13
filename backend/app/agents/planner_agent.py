from app.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.providers.llm.manager import llm_manager
from app.providers.llm.output_parser import output_parser
from app.schemas.planner import (
    PlannerRequest,
    PlannerResponse,
)
from app.core.exceptions import LLMProviderError, OutputParsingError


class PlannerAgent:

    def create_plan(
        self,
        request: PlannerRequest,
    ) -> PlannerResponse:

        user_prompt = f"""
Research Request:

{request.query}

Relevant Previous Research:

{request.previous_research}

Generate a detailed research execution plan.

Return ONLY valid JSON.
"""

        response = llm_manager.generate(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            prompt=user_prompt,
        )

        if not response.success:
            raise LLMProviderError(response.error)

        data = output_parser.parse_json(
            response.content
        )

        if data is None:
            raise OutputParsingError(
                "Planner returned invalid JSON."
            )

        return PlannerResponse(**data)


planner_agent = PlannerAgent()