import time

from app.schemas.llm import LLMResponse


class BaseProvider:

    def start_timer(self) -> float:
        return time.perf_counter()

    def calculate_latency(self, start_time: float) -> float:
        return round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

    def success_response(
        self,
        provider: str,
        model: str,
        content: str,
        latency_ms: float,
        metadata: dict | None = None,
    ) -> LLMResponse:

        return LLMResponse(
            provider=provider,
            model=model,
            content=content,
            success=True,
            latency_ms=latency_ms,
            error=None,
            metadata=metadata or {},
        )

    def error_response(
        self,
        provider: str,
        model: str,
        error: str,
    ) -> LLMResponse:

        return LLMResponse(
            provider=provider,
            model=model,
            content="",
            success=False,
            latency_ms=0.0,
            error=error,
            metadata={},
        )