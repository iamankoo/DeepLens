from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.chunker import semantic_chunker
from app.search.embedder import chunk_embedder
from app.search.retriever import semantic_retriever

url = "https://www.ibm.com/think/topics/langgraph"

text = content_extractor.extract(url)

text = document_normalizer.normalize(text)

chunks = semantic_chunker.chunk(
    text=text,
    title="IBM LangGraph",
    url=url,
)

chunks = chunk_embedder.embed(chunks)

results = semantic_retriever.retrieve(
    query="What is LangGraph?",
    chunks=chunks,
    top_k=3,
)

print()

for chunk in results:

    print("=" * 80)

    print("Similarity:", round(chunk.similarity, 4))

    print()

    print(chunk.text[:400])

    print()