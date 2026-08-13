from app.search.retrieval_manager import retrieval_manager

chunks = retrieval_manager.retrieve(
    query="What is LangGraph?",
    title="IBM",
    url="https://www.ibm.com/think/topics/langgraph",
)

for chunk in chunks:

    print("=" * 80)

    print(chunk.similarity)

    print()

    print(chunk.text[:400])