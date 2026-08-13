from app.providers.llm.gemini_provider import GeminiProvider

provider = GeminiProvider()

response = provider.generate(
    prompt="Explain LangGraph in one paragraph."
)

print(response)