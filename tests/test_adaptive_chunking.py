from pathlib import Path

import pytest

from chunklet import (
    AdaptiveChunker,
    UnsupportedFileTypeError,
)

# --- Helpers ---


def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())


# --- Constants ---

SAMPLE_CODE = "samples/sample_module.py"
SAMPLE_DOCUMENT = "samples/sample_text.txt"

LONG_CODE = "def f():\n    return 1\n" * 40

SOURCES = [SAMPLE_CODE, SAMPLE_DOCUMENT]

# --- Fixtures ---


@pytest.fixture
def chunker():
    """Provide a ready-to-use AdaptiveChunker instance for tests."""
    return AdaptiveChunker(token_counter=simple_token_counter)


# --- Profile Detection Tests ---


@pytest.mark.parametrize(
    ("source", "target", "expected_type"),
    [
        (SAMPLE_DOCUMENT, "note.txt", "document"),
        (SAMPLE_CODE, "module.py", "code"),
        (SAMPLE_CODE, "script", "code"),
    ],
)
def test_source_is_routed_to_expected_profile(
    chunker, tmp_path, source, target, expected_type
):
    """Test that a source file is routed to its expected profile."""
    src = tmp_path / target
    src.write_text(Path(source).read_text())

    chunker.add_file(src)
    chunks = list(chunker.process())

    assert chunks
    assert all(chunk.metadata.inferred_type == expected_type for chunk in chunks)


# --- Learning Tests ---


def test_code_profile_matches_are_learned(chunker, tmp_path):
    """Test that the code profile learns the real source metrics."""
    chunker.add_file(SAMPLE_CODE)
    list(chunker.process())

    assert chunker.learned_state["code"] == {
        "max_lines": pytest.approx(13.05),
        "max_functions": pytest.approx(1.0),
        "max_tokens": pytest.approx(363.875),
    }


def test_document_profile_metrics_are_learned(chunker):
    """Test that the document profile learns the real source metrics."""
    chunker.add_file(SAMPLE_DOCUMENT)
    list(chunker.process())

    assert chunker.learned_state["document"] == {
        "max_sentences": pytest.approx(6.7),
        "header_density_ratio": pytest.approx(0.035),
        "max_section_breaks": pytest.approx(1.0),
        "max_tokens": pytest.approx(395.6),
    }


def test_different_ema_alpha_changes_learned_values():
    """Test that ema_alpha changes how strongly fresh metrics drive the EMA."""
    fresh = AdaptiveChunker(token_counter=simple_token_counter, ema_alpha=1.0)
    frozen = AdaptiveChunker(token_counter=simple_token_counter, ema_alpha=0.0)

    for chunker in (fresh, frozen):
        chunker.add_files(SOURCES)
        list(chunker.process())

    assert fresh.learned_state["code"]["max_lines"] == pytest.approx(8.5)
    assert fresh.learned_state["code"]["max_tokens"] == pytest.approx(18.25)
    assert fresh.learned_state["document"]["max_sentences"] == pytest.approx(6.0)
    assert fresh.learned_state["document"]["max_tokens"] == pytest.approx(124.0)

    assert frozen.learned_state["code"]["max_lines"] == pytest.approx(15.0)
    assert frozen.learned_state["code"]["max_tokens"] == pytest.approx(512.0)
    assert frozen.learned_state["document"]["max_sentences"] == pytest.approx(7.0)
    assert frozen.learned_state["document"]["max_tokens"] == pytest.approx(512.0)


def test_missing_token_counter_skips_max_tokens_learning():
    """Test that max_tokens learning is skipped when no token counter is set."""
    chunker = AdaptiveChunker()
    chunker.add_files(SOURCES)
    chunks = list(chunker.process())

    assert chunks
    assert chunker.learned_state["code"]["max_tokens"] == 512.0
    assert chunker.learned_state["document"]["max_tokens"] == 512.0


# --- Error Handling Tests ---


def test_missing_file_raises_file_not_found(chunker):
    """Test that enqueuing a missing file path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        chunker.add_file("/path/to/nonexistent/file.py")


def test_binary_file_raises_unsupported_type(chunker, tmp_path):
    """Test that an unsupported binary file raises UnsupportedFileTypeError."""
    binary_file = tmp_path / "data.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\xff")

    chunker.add_file(binary_file)
    with pytest.raises(UnsupportedFileTypeError):
        list(chunker.process())


# --- Process / Batch Tests ---


def test_process_on_empty_queue_yields_nothing(chunker):
    """Test that processing an empty queue yields no chunks."""
    assert list(chunker.process()) == []


def test_add_texts_routes_each_source_to_its_profile(chunker):
    """Test that add_texts classifies each raw string independently."""
    chunker.add_texts(
        [Path(SAMPLE_CODE).read_text(), Path(SAMPLE_DOCUMENT).read_text()]
    )
    chunks = list(chunker.process())

    types = {chunk.metadata.inferred_type for chunk in chunks}
    assert types == {"code", "document"}


def test_all_chunks_carry_inferred_type(chunker):
    """Test that every produced chunk is tagged with inferred_type."""
    chunker.add_files(SOURCES)
    chunks = list(chunker.process())

    assert chunks
    for chunk in chunks:
        assert chunk.metadata.inferred_type in {"code", "document"}


def test_separator_is_yielded_between_chunks_per_source(chunker):
    """Test that a separator is yielded between chunks of the same source."""
    chunker.add_files(SOURCES)
    separator = object()
    results = list(chunker.process(separator=separator))

    chunk_count = sum(1 for r in results if r is not separator)
    separator_count = sum(1 for r in results if r is separator)

    assert chunk_count > 1
    assert separator_count == 2
