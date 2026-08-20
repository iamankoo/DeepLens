import time

from fastembed.rerank.cross_encoder import TextCrossEncoder

from app.core.logger import logger

# Xenova/ms-marco-MiniLM-L-6-v2 is an ONNX export of the same
# cross-encoder/ms-marco-MiniLM-L-6-v2 weights this project used via
# sentence-transformers before — same ranking model, no accuracy tradeoff —
# swapped for the reason documented in
# app/memory/providers/sentence_transformer_provider.py: fastembed
# (ONNX Runtime) doesn't need torch, and torch's own baseline import cost
# was a direct, measured contributor to the production worker OOM.
_MODEL_NAME = "Xenova/ms-marco-MiniLM-L-6-v2"


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
            logger.debug("loading cross-encoder model", extra={"model": _MODEL_NAME})
            t0 = time.perf_counter()
            # threads=1: see the identical rationale in
            # app/memory/providers/sentence_transformer_provider.py.
            self._model = TextCrossEncoder(_MODEL_NAME, threads=1)
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
            documents = [chunk.text for chunk in chunks]

            scores = list(self.model.rerank(query, documents))

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

    def unload(self):
        """Frees the loaded ONNX cross-encoder session. Called by
        retrieval_node once it's done — nothing later in the same workflow
        run (writer/verification/rewrite/citation) uses this ranker again,
        and its resident session was a direct, measured contributor to a
        real OOM in a 1GB-limited container: the pipeline was SIGKILLed at
        citation_node's own batch paragraph-embedding call with memory
        already at ~97%, immediately after retrieval_node's cross-encoder
        calls. self.model's lazy-load property means the next research run
        in this same worker process (a fresh job, not this one) will simply
        reload it on first use, at the usual one-time cost."""
        self._model = None


cross_encoder = CrossEncoderRanker()