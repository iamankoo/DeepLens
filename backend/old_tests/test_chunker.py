from app.search.content_extractor import (
    content_extractor,
)

from app.search.document_normalizer import (
    document_normalizer,
)

from app.search.chunker import (
    semantic_chunker,
)

url = "https://www.ibm.com/think/topics/langgraph"

text = content_extractor.extract(url)

text = document_normalizer.normalize(text)

chunks = semantic_chunker.chunk(
    text=text,
    title="IBM LangGraph",
    url=url,
)

print()

print("Chunks:", len(chunks))

print()

for chunk in chunks:

    print("=" * 80)

    print("Chunk:", chunk.chunk_id)

    print(
        f"Sentences: {chunk.start_sentence}-{chunk.end_sentence}"
    )

    print()

    print(chunk.text[:250])

    print()