"""Focused tests for the Chunking Node OOM fix (production incident: worker
work-horse SIGKILLed mid-Chunking-Node on a ~1GB container). Unlike most of
this suite these are deliberately network-free (mocked) — they're checking a
memory-safety bound, not extraction quality, so they shouldn't depend on a
live page's actual size."""

from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.search.content_extractor import ContentExtractor
from app.workflows.nodes import _extract_and_chunk_source


def test_raw_html_download_is_capped():
    """A pathologically large page must not be read into memory past
    MAX_RAW_HTML_BYTES, even though the server offered more."""

    extractor = ContentExtractor()
    # Matches the real chunk_size passed to iter_content() in
    # content_extractor.py, so the overshoot-slack assertion below reflects
    # the real worst case (one chunk past the cap), not an artifact of a
    # differently-sized mock chunk.
    piece_size = 65536
    piece = b"<p>x</p>" * (piece_size // 8)
    num_pieces = (extractor.MAX_RAW_HTML_BYTES // len(piece)) + 5

    mock_response = MagicMock()
    mock_response.encoding = "utf-8"
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [piece] * num_pieces

    with patch("app.search.content_extractor.requests.get", return_value=mock_response):
        with patch("app.search.content_extractor.trafilatura.extract") as mock_trafilatura:
            mock_trafilatura.return_value = "extracted"
            extractor.extract("https://example.com/huge-page")

    # trafilatura must have been called with HTML capped at (or just over,
    # within one chunk_size) MAX_RAW_HTML_BYTES, never the full offered size.
    called_html = mock_trafilatura.call_args.args[0]
    offered_total = len(piece) * num_pieces
    assert len(called_html.encode("utf-8")) <= extractor.MAX_RAW_HTML_BYTES + piece_size
    assert len(called_html.encode("utf-8")) < offered_total
    mock_response.close.assert_called_once()


def test_extracted_text_truncated_before_chunking():
    """chunking_node's per-source worker must cap extracted text at
    settings.MAX_SOURCE_CONTENT_CHARS before it reaches the chunker/embedder,
    regardless of how much content_extractor returned."""

    oversized_text = "word " * (settings.MAX_SOURCE_CONTENT_CHARS * 2)
    source = MagicMock(url="https://example.com/long-article", title="Long Article")

    seen_text = {}

    def fake_normalize(text):
        seen_text["value"] = text
        return text

    with patch("app.workflows.nodes.content_extractor.extract", return_value=oversized_text):
        with patch("app.workflows.nodes.document_normalizer.normalize", side_effect=fake_normalize):
            with patch("app.workflows.nodes.semantic_chunker.chunk", return_value=[]):
                _extract_and_chunk_source(source, 1, 1)

    assert len(seen_text["value"]) <= settings.MAX_SOURCE_CONTENT_CHARS


def test_short_text_not_truncated():
    """A normal, well-under-the-cap source must pass through unchanged."""

    short_text = "This is a normal-length article." * 20
    assert len(short_text) < settings.MAX_SOURCE_CONTENT_CHARS
    source = MagicMock(url="https://example.com/short-article", title="Short Article")

    seen_text = {}

    def fake_normalize(text):
        seen_text["value"] = text
        return text

    with patch("app.workflows.nodes.content_extractor.extract", return_value=short_text):
        with patch("app.workflows.nodes.document_normalizer.normalize", side_effect=fake_normalize):
            with patch("app.workflows.nodes.semantic_chunker.chunk", return_value=[]):
                _extract_and_chunk_source(source, 1, 1)

    assert seen_text["value"] == short_text


def test_chunking_concurrency_and_source_cap_come_from_settings():
    """EXTRACTION_WORKERS / MAX_SOURCES_FOR_CHUNKING must be the configured
    Settings values, not silently-reintroduced hardcoded constants — this is
    what makes the production-vs-dev conservative default actually apply."""

    from app.workflows import nodes

    assert nodes.EXTRACTION_WORKERS == settings.EXTRACTION_WORKERS
    assert nodes.MAX_SOURCES_FOR_CHUNKING == settings.MAX_SOURCES_FOR_CHUNKING
