from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.chunker import semantic_chunker


def test_chunker():

    print("Testing Content Extractor and Semantic Chunker...")

    url = "https://www.ibm.com/think/topics/langgraph"

    text = content_extractor.extract(url)

    assert text is not None, "Extraction failed"

    text = document_normalizer.normalize(text)

    chunks = semantic_chunker.chunk(
        text=text,
        title="IBM LangGraph",
        url=url,
    )

    assert len(chunks) > 0, "Chunking failed"

    assert chunks[0].text != "", "Empty chunk text"

    print(f"Chunker works. Created {len(chunks)} chunks.")


if __name__ == "__main__":

    test_chunker()
