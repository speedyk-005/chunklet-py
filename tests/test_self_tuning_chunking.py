from pathlib import Path

import pytest

from chunklet import (
    SelfTuningChunker,
    UnsupportedFileTypeError,
)

# --- Helpers ---


def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())


# --- Constants ---

SAMPLE_CODE = "samples/sample_module.py"
SAMPLE_DOCUMENT = "samples/sample_text.txt"

SOURCES = [SAMPLE_CODE, SAMPLE_DOCUMENT]

# --- Fixtures ---


@pytest.fixture
def chunker():
    """Provide a ready-to-use SelfTuningChunker instance for tests."""
    return SelfTuningChunker(lang="en", token_counter=simple_token_counter)


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
        "max_lines": pytest.approx(14.58, rel=1e-3),
        "max_functions": pytest.approx(1.0),
        "max_tokens": pytest.approx(480.14, rel=1e-3),
    }


def test_document_profile_metrics_are_learned(chunker):
    """Test that the document profile learns the real source metrics."""
    chunker.add_file(SAMPLE_DOCUMENT)
    list(chunker.process())

    assert chunker.learned_state["document"] == {
        "max_sentences": pytest.approx(6.93, rel=1e-2),
        "header_density_ratio": pytest.approx(0.0468, rel=1e-2),
        "max_section_breaks": pytest.approx(1.0),
        "max_tokens": pytest.approx(486.96, rel=1e-2),
    }


def test_missing_token_counter_skips_max_tokens_learning():
    """Test that max_tokens learning is skipped when no token counter is set."""
    chunker = SelfTuningChunker(lang="en")
    chunker.add_files(SOURCES)
    chunks = list(chunker.process())

    assert chunks
    assert chunker.learned_state["code"]["max_tokens"] == 512.0
    assert chunker.learned_state["document"]["max_tokens"] == 512.0


def test_initial_state_seeds_learned_profiles():
    """Test that a provided baseline becomes the starting point for learning."""
    baseline = {
        "code": {"max_lines": 40.0, "max_functions": 2, "max_tokens": 256.0},
        "document": {
            "max_sentences": 12.0,
            "header_density_ratio": 0.2,
            "max_section_breaks": 2,
            "max_tokens": 256.0,
        },
    }
    chunker = SelfTuningChunker(
        lang="en", token_counter=simple_token_counter, initial_state=baseline
    )
    chunker.add_files(SOURCES)
    list(chunker.process())

    assert chunker.learned_state == {
        "code": {
            "max_lines": pytest.approx(37.96, rel=1e-3),
            "max_functions": pytest.approx(1.93, rel=1e-2),
            "max_tokens": pytest.approx(240.66, rel=1e-3),
        },
        "document": {
            "max_sentences": pytest.approx(11.61, rel=1e-3),
            "header_density_ratio": pytest.approx(0.187, rel=1e-2),
            "max_section_breaks": pytest.approx(1.93, rel=1e-2),
            "max_tokens": pytest.approx(247.48, rel=1e-3),
        },
    }


def test_initial_state_fills_missing_metrics_with_defaults():
    """Test that omitted profiles and metrics fall back to defaults."""
    chunker = SelfTuningChunker(lang="en", initial_state={"code": {"max_lines": 42.0}})

    assert chunker.learned_state["code"]["max_lines"] == 42.0
    assert chunker.learned_state["code"]["max_functions"] == 1
    assert chunker.learned_state["code"]["max_tokens"] == 512.0
    assert chunker.learned_state["document"] == {
        "max_sentences": 7.0,
        "header_density_ratio": 0.05,
        "max_section_breaks": 1,
        "max_tokens": 512.0,
    }


def test_initial_state_with_unknown_profile_raises():
    """Test that an unknown profile name in initial_state raises ValueError."""
    with pytest.raises(ValueError, match="Unknown profile 'spreadsheet'"):
        SelfTuningChunker(lang="en", initial_state={"spreadsheet": {"max_rows": 3}})


def test_hard_token_limit_caps_learned_max_tokens(tmp_path, monkeypatch):
    """Test that hard_token_limit caps the learned max_tokens at chunk time."""
    chunker = SelfTuningChunker(
        lang="en", token_counter=simple_token_counter, hard_token_limit=128
    )
    monkeypatch.setitem(chunker.learned_state["code"], "max_tokens", 100_000)
    monkeypatch.setitem(chunker.learned_state["document"], "max_tokens", 100_000)

    chunker.add_files(SOURCES)
    chunks = list(chunker.process())

    assert chunks
    assert chunker.code_chunker.max_tokens == 128
    assert chunker.document_chunker.max_tokens == 128
    assert all(simple_token_counter(chunk.content) <= 128 for chunk in chunks)


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
    results = list(chunker.process(separator=separator, show_progress=True))

    chunk_count = sum(1 for r in results if r is not separator)
    separator_count = sum(1 for r in results if r is separator)

    assert chunk_count > 1
    assert separator_count == 2
