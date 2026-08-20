from fastembed import TextEmbedding

from app.memory.embedding_provider import BaseEmbeddingProvider

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class _FastEmbedModelAdapter:
    """Mimics the one slice of sentence-transformers' SentenceTransformer.encode()
    interface this project's call sites rely on — app/search/embedder.py,
    app/citations/injector.py, and app/intelligence/evidence.py all reach
    into `sentence_transformer_provider.model.encode(texts,
    normalize_embeddings=True, show_progress_bar=False, batch_size=N)`
    directly, not through embed() below. Kept as a same-signature shim so
    none of those call sites needed to change, confining the fastembed
    migration entirely to this module. normalize_embeddings/
    show_progress_bar are accepted but unused: fastembed's TextEmbedding
    already L2-normalizes its output by default (verified live — unit
    norm), matching normalize_embeddings=True's effect, and it has no
    progress-bar output to suppress."""

    def __init__(self, fastembed_model: TextEmbedding):
        self._model = fastembed_model

    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False, batch_size=64):
        single_input = isinstance(texts, str)
        result = list(self._model.embed([texts] if single_input else texts, batch_size=batch_size))
        return result[0] if single_input else result


class SentenceTransformerProvider(BaseEmbeddingProvider):

    def __init__(self):
        # fastembed (ONNX Runtime) instead of sentence-transformers (PyTorch)
        # — both load the exact same all-MiniLM-L6-v2 weights, but
        # fastembed's import + loaded-model memory footprint is roughly a
        # third of torch + sentence-transformers'. Measured live in a real
        # container reproducing this project's production ~1GB worker
        # limit: torch alone costs ~207MB at import, sentence-transformers
        # (transformers/tokenizers/numpy on top) another ~166MB, and loading
        # the model itself another ~107MB — versus fastembed's ~67MB import
        # + ~162MB loaded model, ~280MB less for the same embedding
        # capability. That baseline gap was the real, measured cause of
        # Chunking Node's OOM even after every concurrency/content-size
        # limit tried before this (see the "Research pipeline resource
        # limits" section in app/core/config.py) — this container's
        # *baseline* memory before any job-specific work even started was
        # already 74-98% of the 1GB limit, reproduced live via
        # `docker run --memory=1g` against this exact image processing a
        # real request: SIGKILLed at 98% right as Chunking began embedding,
        # despite every job-level limit already being as tight as this
        # pipeline's output quality could tolerate.
        # threads=1: caps ONNX Runtime's intra-op thread pool for this
        # session — reproduced live that the default (one thread per CPU
        # core) contributes real, avoidable memory/CPU overhead in a
        # single-job-at-a-time worker where multi-threaded inference buys
        # no real latency win, mirroring why app/worker.py also caps
        # OMP/MKL thread counts via env vars for the same reason.
        self._raw_model = TextEmbedding(_MODEL_NAME, threads=1)
        self.model = _FastEmbedModelAdapter(self._raw_model)

    def provider_name(self) -> str:
        return "FastEmbed"

    def embed(self, text: str) -> list[float]:
        embedding = next(iter(self._raw_model.embed([text])))
        return embedding.tolist()


sentence_transformer_provider = SentenceTransformerProvider()
