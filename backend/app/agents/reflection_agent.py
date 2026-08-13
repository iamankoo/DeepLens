from app.prompts.reflection import REFLECTION_SYSTEM_PROMPT
from app.providers.llm.manager import llm_manager
from app.providers.llm.output_parser import output_parser
from app.schemas.reflection import (
    ReflectionRequest,
    ReflectionResponse,
)
from app.core.exceptions import LLMProviderError, OutputParsingError


class ReflectionAgent:

    def review(
        self,
        request: ReflectionRequest,
    ) -> ReflectionResponse:

        user_prompt = f"""
Research Objective:

{request.objective}

Research Report:

{request.report}

Review this report.

Return ONLY valid JSON.
"""

        response = llm_manager.generate(
            system_prompt=REFLECTION_SYSTEM_PROMPT,
            prompt=user_prompt,
        )

        if not response.success:
            raise LLMProviderError(response.error)

        data = output_parser.parse_json(
            response.content
        )

        if data is None:
            raise OutputParsingError(
                "Reflection returned invalid JSON."
            )

        return ReflectionResponse(
            **data
        )


reflection_agent = ReflectionAgent()