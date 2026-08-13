from app.search.retrieval_manager import retrieval_manager
from app.search.cross_encoder import cross_encoder

chunks = retrieval_manager.retrieve(
    query="What is LangGraph?",
    title="IBM",
    url="https://www.ibm.com/think/topics/langgraph",
    top_k=10,
)

ranked = cross_encoder.rerank(
    "What is LangGraph?",
    chunks,
)

for chunk, score in ranked:

    print("=" * 80)

    print("Cross Score:", round(float(score), 4))

    print()

    print(chunk.text[:300])