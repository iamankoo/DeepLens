from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.chunker import semantic_chunker
from app.search.embedder import chunk_embedder
from app.search.retriever import semantic_retriever


def test_retriever():

    print("Testing Semantic Retriever...")

    url = "https://www.ibm.com/think/topics/langgraph"

    text = content_extractor.extract(url)

    text = document_normalizer.normalize(text)

    chunks = semantic_chunker.chunk(
        text=text,
        title="IBM LangGraph",
        url=url,
    )

    chunks = chunk_embedder.embed(chunks)

    retrieved = semantic_retriever.retrieve(
        query="What is LangGraph used for?",
        chunks=chunks,
        top_k=3,
    )

    assert len(retrieved) > 0, "No chunks retrieved"

    assert retrieved[0].similarity > 0, "Similarity score is 0"

    print(f"Retriever works. Retrieved {len(retrieved)} chunks.")


if __name__ == "__main__":

    test_retriever()
