import time

from sentence_transformers import CrossEncoder

from app.core.logger import logger


class CrossEncoderRanker:

    def __init__(self):
        logger.debug("loading cross-encoder model", extra={"model": "cross-encoder/ms-marco-MiniLM-L-6-v2"})
        t0 = time.perf_counter()
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
        elapsed = time.perf_counter() - t0
        logger.debug("cross-encoder model loaded", extra={"elapsed_s": round(elapsed, 2)})

    def rerank(
        self,
        query,
        chunks,
    ):
        if not chunks:
            return []

        logger.debug("reranking chunks", extra={"chunk_count": len(chunks)})
        t0 = time.perf_counter()

        try:
            pairs = [
                (query, chunk.text)
                for chunk in chunks
            ]

            scores = self.model.predict(pairs)

        except Exception as e:
            logger.error("error during cross-encoder predict", extra={"error": str(e)})
            # Fallback: return chunks with score 0.0
            return [(chunk, 0.0) for chunk in chunks]

        ranked = list(zip(chunks, scores))

        ranked.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        elapsed = time.perf_counter() - t0
        logger.debug("reranked chunks", extra={"chunk_count": len(chunks), "elapsed_s": round(elapsed, 2)})

        return ranked


cross_encoder = CrossEncoderRanker()