from app.memory.providers.sentence_transformer_provider import (
    sentence_transformer_provider,
)

embedding = sentence_transformer_provider.embed(
    "LangGraph is an orchestration framework for AI agents."
)

print(type(embedding))
print(len(embedding))
print(embedding[:10])