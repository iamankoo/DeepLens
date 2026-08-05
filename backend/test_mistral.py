from app.providers.llm.mistral_provider import MistralProvider

provider = MistralProvider()

response = provider.generate(
    prompt="Explain LangGraph in one paragraph."
)

print(response)