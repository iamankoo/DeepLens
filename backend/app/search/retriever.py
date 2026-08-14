import time

import numpy as np

from app.core.logger import logger
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

        logger.debug("embedding query and scoring chunks", extra={"chunk_count": len(chunks)})
        t0 = time.perf_counter()

        try:
            query_embedding = np.array(
                sentence_transformer_provider.embed(query)
            )
        except Exception as e:
            logger.error("error embedding query", extra={"error": str(e)})
            return []

        valid_chunks = []
        for chunk in chunks:
            if chunk.embedding is None:
                # Skip chunks whose embeddings were stripped (e.g. by evidence engine)
                continue
            valid_chunks.append(chunk)

        logger.debug("valid embedded chunks", extra={"valid": len(valid_chunks), "total": len(chunks)})

        for chunk in valid_chunks:
            try:
                chunk_embedding = np.array(chunk.embedding)
                chunk.similarity = float(np.dot(query_embedding, chunk_embedding))
            except Exception as e:
                logger.error("error scoring chunk", extra={"error": str(e)})
                chunk.similarity = 0.0

        ranked = chunk_ranker.rank(
            query=query,
            chunks=valid_chunks,
        )

        elapsed = time.perf_counter() - t0
        logger.debug(
            "retrieved top chunks",
            extra={"top_k": min(top_k, len(ranked)), "elapsed_s": round(elapsed, 2)},
        )

        return ranked[:top_k]


semantic_retriever = SemanticRetriever()