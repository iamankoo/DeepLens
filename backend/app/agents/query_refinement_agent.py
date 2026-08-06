from app.prompts.query_refinement import QUERY_REFINEMENT_SYSTEM_PROMPT
from app.providers.llm.manager import llm_manager
from app.providers.llm.output_parser import output_parser
from app.schemas.query_refinement import (
    QueryRefinementRequest,
    QueryRefinementResponse,
)


class QueryRefinementAgent:

    def generate_queries(
        self,
        request: QueryRefinementRequest,
    ) -> QueryRefinementResponse:

        user_prompt = f"""
Research Objective:

{request.objective}

Previous Search Queries:

{request.previous_queries}

Missing Information:

{request.missing_information}

Generate better search queries.

Return ONLY JSON.
"""

        response = llm_manager.generate(
            system_prompt=QUERY_REFINEMENT_SYSTEM_PROMPT,
            prompt=user_prompt,
        )

        if not response.success:
            raise Exception(response.error)

        data = output_parser.parse_json(
            response.content
        )

        if data is None:
            raise Exception(
                "Query Refinement returned invalid JSON."
            )

        return QueryRefinementResponse(**data)


query_refinement_agent = QueryRefinementAgent()