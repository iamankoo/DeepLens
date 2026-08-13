from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.chunker import semantic_chunker
from app.search.embedder import chunk_embedder

url = "https://www.ibm.com/think/topics/langgraph"

text = content_extractor.extract(url)

text = document_normalizer.normalize(text)

chunks = semantic_chunker.chunk(
    text=text,
    title="IBM LangGraph",
    url=url,
)

chunks = chunk_embedder.embed(chunks)

print()

print("Chunks:", len(chunks))

print()

for chunk in chunks:

    print("=" * 70)

    print("Chunk:", chunk.chunk_id)

    print("Embedding:", len(chunk.embedding))

    print(chunk.text[:120])

    print()