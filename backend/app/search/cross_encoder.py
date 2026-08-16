import time

from sentence_transformers import CrossEncoder

from app.core.logger import logger


class CrossEncoderRanker:

    def __init__(self):
        self._model = None

    @property
    def model(self):
        # Lazy on purpose: this ranker isn't used until retrieval_node, which
        # runs after chunking_node — the node that downloads full source
        # pages and embeds them, and the one that was OOM-SIGKILLed in
        # production on the ~1GB worker container. Loading this model eagerly
        # at import time (as app.worker.py's model-preload fix originally did
        # for both models — see its docstring) meant the cross-encoder's
        # weights sat resident in memory throughout chunking_node's own
        # peak-memory window despite being needed nowhere near it. Deferring
        # the load to first actual use frees that headroom for exactly the
        # node that needs it; app.worker.py's preload still covers the
        # embedder (app/search/embedder.py), which chunking_node's own
        # immediate next step does need.
        if self._model is None:
            logger.debug("loading cross-encoder model", extra={"model": "cross-encoder/ms-marco-MiniLM-L-6-v2"})
            t0 = time.perf_counter()
            self._model = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2"
            )
            elapsed = time.perf_counter() - t0
            logger.debug("cross-encoder model loaded", extra={"elapsed_s": round(elapsed, 2)})
        return self._model

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