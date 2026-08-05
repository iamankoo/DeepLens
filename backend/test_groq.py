from app.providers.llm.groq_provider import GroqProvider

provider = GroqProvider()

response = provider.generate(
    prompt="Explain LangGraph in one paragraph."
)

print(response)