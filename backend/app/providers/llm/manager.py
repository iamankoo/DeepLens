import time
import traceback

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

        print("\n[LLMManager] ====================================================")
        print("[LLMManager] generate() called")
        print(f"[LLMManager] Prompt length : {len(prompt)}")
        print(f"[LLMManager] Max tokens   : {max_tokens}")
        print(f"[LLMManager] Temperature  : {temperature}")

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
            print(f"[LLMManager] Completed in {elapsed:.2f}s")
            print("[LLMManager] ====================================================\n")

            return response

        except Exception:
            elapsed = time.perf_counter() - start
            print(f"[LLMManager] FAILED after {elapsed:.2f}s")
            print(traceback.format_exc())
            raise


llm_manager = LLMManager()