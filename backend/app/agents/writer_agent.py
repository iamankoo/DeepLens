from app.prompts.writer import WRITER_SYSTEM_PROMPT
from app.providers.llm.manager import llm_manager
from app.schemas.writer import WriterRequest, WriterResponse


class WriterAgent:

    def generate_report(
        self,
        request: WriterRequest,
    ) -> WriterResponse:

        sources_text = ""

        for index, source in enumerate(request.sources, start=1):

            title = source.get("title", "Unknown Title")
            url = source.get("url", "")
            content = source.get("content", "")

            sources_text += f"""
Source {index}

Title:
{title}

URL:
{url}

Content:
{content}

------------------------------------
"""

        user_prompt = f"""
Research Objective:

{request.objective}

Research Tasks:

{request.tasks}

Research Sources:

{sources_text}

Write a professional research report.
"""

        response = llm_manager.generate(
            system_prompt=WRITER_SYSTEM_PROMPT,
            prompt=user_prompt,
        )

        if not response.success:
            raise Exception(response.error)

        return WriterResponse(
            report=response.content
        )


writer_agent = WriterAgent()