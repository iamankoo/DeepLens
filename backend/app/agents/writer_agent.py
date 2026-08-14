from app.core.logger import logger
from app.prompts.writer import WRITER_SYSTEM_PROMPT
from app.providers.llm.manager import llm_manager
from app.schemas.writer import WriterRequest, WriterResponse
from app.citations.extractor import citation_extractor
from app.citations.reference_manager import reference_manager
from app.core.exceptions import LLMProviderError


class WriterAgent:

    def generate_report(
        self,
        request: WriterRequest,
    ) -> WriterResponse:

        context_text = request.context

        if not context_text:
            sources_text = ""
            for index, source in enumerate(request.sources, start=1):
                sources_text += f"""
Source {index}

Title:
{source.title}

Source:
{source.source}

URL:
{source.url}

Credibility Score:
{source.credibility_score}

Content:
{source.snippet}

------------------------------------
"""
            context_text = sources_text

        # Cap context to avoid excessive LLM latency (12k chars ~3k tokens)
        MAX_CONTEXT_CHARS = 12_000
        if len(context_text) > MAX_CONTEXT_CHARS:
            logger.debug(
                "capping context",
                extra={"original_chars": len(context_text), "max_chars": MAX_CONTEXT_CHARS},
            )
            context_text = context_text[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated for brevity]"

        user_prompt = f"""
Research Objective:

{request.objective}

Research Tasks:

{request.tasks}

Research Context (structured evidence grouped by task):

{context_text}

Instructions:

1. Use the provided context as evidence.
2. Organize the report with clear headings.
3. Write professionally and objectively.
4. Do not invent facts.
5. Reference the sources naturally where appropriate.
6. Do NOT generate a References section.

Write a comprehensive research report.
"""

        import time as _time
        logger.debug("sending prompt to LLM", extra={"prompt_chars": len(user_prompt)})
        _t0 = _time.perf_counter()

        response = llm_manager.generate(
            system_prompt=WRITER_SYSTEM_PROMPT,
            prompt=user_prompt,
        )

        logger.debug("LLM responded", extra={"elapsed_s": round(_time.perf_counter() - _t0, 2)})

        if not response.success:
            raise LLMProviderError(response.error)

        citations = citation_extractor.extract(
            request.sources
        )

        references = reference_manager.generate(
            citations.citations,
            style="APA",
        )

        final_report = f"{response.content}\n\n---\n\n# References\n\n{references}"

        return WriterResponse(
            report=final_report
        )


writer_agent = WriterAgent()