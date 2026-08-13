from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.chunker import semantic_chunker
from app.search.embedder import chunk_embedder
from app.search.retriever import semantic_retriever
from app.search.cross_encoder import cross_encoder


def test_cross_encoder():

    print("Testing Cross Encoder Ranker...")

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
        query="LangGraph framework description",
        chunks=chunks,
        top_k=10,
    )

    reranked = cross_encoder.rerank(
        query="LangGraph framework description",
        chunks=retrieved,
    )

    assert len(reranked) > 0, "No chunks reranked"

    assert reranked[0][1] is not None, "Rerank score is None"

    print("Cross Encoder works successfully.")


if __name__ == "__main__":

    test_cross_encoder()
