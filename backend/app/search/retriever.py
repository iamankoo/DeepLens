import time

import numpy as np

from app.memory.providers.sentence_transformer_provider import (
    sentence_transformer_provider,
)
from app.search.chunk import SearchChunk
from app.search.ranker import chunk_ranker


class SemanticRetriever:

    def retrieve(
        self,
        query: str,
        chunks: list[SearchChunk],
        top_k: int = 3,
    ) -> list[SearchChunk]:

        if not chunks:
            return []

        print(f"    [SemanticRetriever] Embedding query, scoring {len(chunks)} chunks...")
        t0 = time.perf_counter()

        try:
            query_embedding = np.array(
                sentence_transformer_provider.embed(query)
            )
        except Exception as e:
            print(f"    [SemanticRetriever] ERROR embedding query: {e}")
            return []

        valid_chunks = []
        for chunk in chunks:
            if chunk.embedding is None:
                # Skip chunks whose embeddings were stripped (e.g. by evidence engine)
                continue
            valid_chunks.append(chunk)

        print(f"    [SemanticRetriever] Valid (embedded) chunks: {len(valid_chunks)}/{len(chunks)}")

        for chunk in valid_chunks:
            try:
                chunk_embedding = np.array(chunk.embedding)
                chunk.similarity = float(np.dot(query_embedding, chunk_embedding))
            except Exception as e:
                print(f"    [SemanticRetriever] ERROR scoring chunk: {e}")
                chunk.similarity = 0.0

        ranked = chunk_ranker.rank(
            query=query,
            chunks=valid_chunks,
        )

        elapsed = time.perf_counter() - t0
        print(f"    [SemanticRetriever] Retrieved top-{min(top_k, len(ranked))} in {elapsed:.2f}s")

        return ranked[:top_k]


semantic_retriever = SemanticRetriever()