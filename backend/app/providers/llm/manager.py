import time
import traceback

from app.core.logger import logger
from app.providers.llm.inference_engine import inference_engine
from app.schemas.llm import LLMResponse


class LLMManager:

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        preferred_providers: list[str] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:

        start = time.perf_counter()

        try:
            response = inference_engine.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                preferred_providers=preferred_providers,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            elapsed = time.perf_counter() - start
            logger.debug("llm_manager.generate() completed", extra={"elapsed_s": round(elapsed, 2)})

            return response

        except Exception:
            elapsed = time.perf_counter() - start
            logger.error(
                "llm_manager.generate() failed",
                extra={"elapsed_s": round(elapsed, 2), "traceback": traceback.format_exc()},
            )
            raise


llm_manager = LLMManager()
