from app.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.providers.llm.manager import llm_manager
from app.providers.llm.output_parser import output_parser
from app.schemas.planner import PlannerResponse


class PlannerAgent:

    def create_plan(self, query: str) -> PlannerResponse:

        user_prompt = f"""
Research Request:

{query}

Generate a research execution plan.
Return ONLY valid JSON.
"""

        response = llm_manager.generate(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            prompt=user_prompt,
        )

        if not response.success:
            raise Exception(response.error)

        data = output_parser.parse_json(
            response.content
        )

        if data is None:
            raise Exception(
                "Planner returned invalid JSON."
            )

        return PlannerResponse(
            **data
        )


planner_agent = PlannerAgent()