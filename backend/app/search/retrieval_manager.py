import time

from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.chunker import semantic_chunker
from app.search.embedder import chunk_embedder
from app.search.retriever import semantic_retriever
from app.search.cross_encoder import cross_encoder


class RetrievalManager:

    def retrieve(
        self,
        query: str,
        title: str,
        url: str,
        top_k: int = 3,
    ):
        print(f"      [RetrievalManager] Retrieving: {url[:80]}")
        t0 = time.perf_counter()

        # 1. Extract
        text = content_extractor.extract(url)
        if not text:
            print(f"      [RetrievalManager] No text extracted — skipping")
            return []

        # 2. Normalize
        text = document_normalizer.normalize(text)

        # 3. Chunk
        t1 = time.perf_counter()
        chunks = semantic_chunker.chunk(
            text=text,
            title=title,
            url=url,
        )
        print(f"      [RetrievalManager] {len(chunks)} chunks in {time.perf_counter()-t1:.2f}s")

        if not chunks:
            return []

        # 4. Embed
        t1 = time.perf_counter()
        chunks = chunk_embedder.embed(chunks)
        print(f"      [RetrievalManager] Embedded in {time.perf_counter()-t1:.2f}s")

        # 5. Retrieve (semantic)
        t1 = time.perf_counter()
        retrieved = semantic_retriever.retrieve(
            query=query,
            chunks=chunks,
            top_k=20,
        )
        print(f"      [RetrievalManager] Retrieved {len(retrieved)} in {time.perf_counter()-t1:.2f}s")

        if not retrieved:
            return []

        # 6. Rerank
        t1 = time.perf_counter()
        reranked = cross_encoder.rerank(
            query=query,
            chunks=retrieved,
        )
        print(f"      [RetrievalManager] Reranked in {time.perf_counter()-t1:.2f}s")

        final_chunks = []
        for chunk, score in reranked[:top_k]:
            chunk.similarity = float(score)
            final_chunks.append(chunk)

        elapsed = time.perf_counter() - t0
        print(f"      [RetrievalManager] Done — {len(final_chunks)} final chunks in {elapsed:.2f}s")
        return final_chunks


retrieval_manager = RetrievalManager()