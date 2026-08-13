from app.providers.llm.inference_engine import inference_engine

response = inference_engine.generate(
    preferred_providers=[
        "groq",
        "gemini",
        "ollama",
    ],
    prompt="Explain LangGraph."
)

print(response)