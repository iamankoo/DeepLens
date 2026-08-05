from app.providers.llm.manager import llm_manager

response = llm_manager.generate(
    prompt="Explain what LangGraph is.",
)

print(response)