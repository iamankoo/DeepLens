import time

from app.core.logger import logger
from app.prompts.rewrite import REWRITE_SYSTEM_PROMPT
from app.providers.llm.manager import llm_manager
from app.rewrite.schemas import (
    RewriteResponse,
    RewriteTask,
)
from app.core.exceptions import LLMProviderError


class RewriteAgent:

    def rewrite(
        self,
        task: RewriteTask,
    ) -> RewriteResponse:

        logger.debug(
            "rewriting paragraph",
            extra={
                "paragraph_index": task.paragraph_index,
                "strategy": task.rewrite_strategy.value,
                "evidence_level": task.evidence_level.value,
            },
        )

        source_text = ""

        if task.source:
            source_text = f"""
Title:
{task.source.title}

Source:
{task.source.source}

Evidence:
{task.source.snippet}

URL:
{task.source.url}
"""

        user_prompt = f"""
Rewrite Strategy:
{task.rewrite_strategy.value}

Evidence Level:
{task.evidence_level.value}

Original Paragraph:
{task.original_paragraph}

Supporting Evidence:
{source_text}

Instructions:

- Preserve all correct information.
- Replace unsupported or hallucinated claims with verified facts from the evidence.
- Do NOT simply negate incorrect statements.
- Do NOT mention that information is unsupported.
- Do NOT explain your changes.
- Do NOT mention the evidence or source.
- If the paragraph contains false information, replace it with the closest verified information from the evidence.
- Keep the paragraph concise.
- Preserve the original writing style.

Return ONLY the corrected paragraph.
"""

        t0 = time.perf_counter()
        logger.debug("calling LLM")

        try:
            response = llm_manager.generate(
                system_prompt=REWRITE_SYSTEM_PROMPT,
                prompt=user_prompt,
            )
        except Exception as e:
            logger.error("LLM call failed", extra={"error": str(e)})
            raise

        elapsed = time.perf_counter() - t0

        if not response.success:
            logger.error("LLM returned failure", extra={"error": response.error})
            raise LLMProviderError(response.error)

        rewritten = response.content.strip()
        logger.debug(
            "paragraph rewritten",
            extra={"elapsed_s": round(elapsed, 2), "output_chars": len(rewritten)},
        )

        return RewriteResponse(
            paragraph_index=task.paragraph_index,
            rewritten_paragraph=rewritten,
        )


rewrite_agent = RewriteAgent()