from pydantic import BaseModel


class LLMResponse(BaseModel):
    provider: str
    model: str

    content: str

    success: bool

    latency_ms: float

    finish_reason: str | None = None

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    error: str | None = None