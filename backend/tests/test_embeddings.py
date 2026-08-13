from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.chunker import semantic_chunker
from app.search.embedder import chunk_embedder


def test_embeddings():

    print("Testing Chunk Embedding...")

    url = "https://www.ibm.com/think/topics/langgraph"

    text = content_extractor.extract(url)

    text = document_normalizer.normalize(text)

    chunks = semantic_chunker.chunk(
        text=text,
        title="IBM LangGraph",
        url=url,
    )

    embedded_chunks = chunk_embedder.embed(chunks)

    assert len(embedded_chunks) > 0, "No chunks embedded"

    assert embedded_chunks[0].embedding is not None, "Embedding is None"

    assert len(embedded_chunks[0].embedding) == 384, f"Invalid embedding dimension: {len(embedded_chunks[0].embedding)}"

    print("Embeddings work successfully.")


if __name__ == "__main__":

    test_embeddings()
