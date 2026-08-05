from app.providers.llm.ollama_provider import OllamaProvider

provider = OllamaProvider()

print("Available:", provider.is_available())

response = provider.generate(
    "Who are you?"
)

print(response)