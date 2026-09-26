import copy
from collections.abc import Generator
from pathlib import Path

import pytest

from chunklet import (
    SelfTuningChunker,
    UnsupportedFileTypeError,
)
from chunklet.exceptions import FileProcessingError

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

    chunks = chunker.chunk_file(src)

    assert chunks
    assert all(chunk.metadata.inferred_type == expected_type for chunk in chunks)


def test_explicit_file_type_overrides_detection(chunker):
    """Test that an explicit file_type is used even when it contradicts the content."""
    code_text = Path(SAMPLE_CODE).read_text()
    assert chunker._detect_file_type(code_text) == "code"

    before = copy.deepcopy(chunker.learned_state)
    chunks = chunker.chunk_text(
        code_text, file_type="document", base_metadata={"real_type": "code"}
    )
    first_chunk = chunks[0]

    assert chunks
    assert first_chunk.metadata.inferred_type == "document"
    assert first_chunk.metadata.real_type == "code"

    # forced to document, so the document profile learns and code is left alone
    assert chunker.learned_state["document"] != before["document"]
    assert chunker.learned_state["code"] == before["code"]


# --- Learning Tests ---


def test_code_profile_matches_are_learned(chunker):
    """Test that the code profile learns the real source metrics."""
    chunks = chunker.chunk_file(SAMPLE_CODE)

    assert chunks
    assert chunker.learned_state["code"] == {
        "max_lines": pytest.approx(14.58, rel=1e-3),
        # the sample spaces functions 8.5 lines apart, above the 7.5 threshold, so the
        # observation is 1 -- identical to the default, so the history is the only proof
        "max_functions": 1,
        "max_tokens": pytest.approx(480.14, rel=1e-3),
    }
    assert chunker.histories[("code", "max_functions")] == [1]


def test_dense_code_learns_two_functions_per_chunk(chunker):
    """Test that tightly packed functions move max_functions off its default."""
    dense_code = "\n".join(f"def f{i}():\n    return {i}" for i in range(12))

    chunks = chunker.chunk_text(dense_code, file_type="code")

    assert chunks
    # 2 lines apart, under the 7.5 threshold, so the observation is 2
    assert chunker.histories[("code", "max_functions")] == [2]
    assert chunker.learned_state["code"]["max_functions"] == pytest.approx(
        1.0645, rel=1e-3
    )


def test_document_profile_metrics_are_learned(chunker):
    """Test that the document profile learns the real source metrics."""
    chunks = chunker.chunk_file(SAMPLE_DOCUMENT)

    assert chunks
    assert chunker.learned_state["document"] == {
        "max_sentences": pytest.approx(6.9355, rel=1e-4),
        "header_density_ratio": pytest.approx(0.0468, rel=1e-2),
        # the sample's header density is 0.047, far below the 0.75 threshold, so the
        # observation is 1 -- identical to the default, hence the history assertion
        "max_section_breaks": 1,
        "max_tokens": pytest.approx(486.96, rel=1e-2),
    }
    assert chunker.histories[("document", "max_section_breaks")] == [1]


def test_header_dense_document_learns_two_section_breaks(chunker):
    """Test that header-dense prose moves max_section_breaks off its default."""
    marker_doc = "\n\n".join(f"## Section {i}\nsome body text here." for i in range(10))

    chunks = chunker.chunk_text(marker_doc, file_type="document")

    assert chunks
    # every paragraph opens with a header, so density clears 0.75 and the signal is 2
    assert chunker.histories[("document", "max_section_breaks")] == [2]
    assert chunker.learned_state["document"]["max_section_breaks"] == pytest.approx(
        1.0645, rel=1e-3
    )


def test_missing_token_counter_skips_max_tokens_learning():
    """Test that max_tokens learning is skipped when no token counter is set."""
    chunker = SelfTuningChunker(lang="en")
    chunks = chunker.chunk_file(SAMPLE_CODE) + chunker.chunk_file(SAMPLE_DOCUMENT)

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
    chunker.chunk_file(SAMPLE_CODE)
    chunker.chunk_file(SAMPLE_DOCUMENT)

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


def test_hard_token_limit_caps_learned_max_tokens(monkeypatch):
    """Test that hard_token_limit caps the learned max_tokens at chunk time."""
    chunker = SelfTuningChunker(
        lang="en", token_counter=simple_token_counter, hard_token_limit=128
    )
    monkeypatch.setitem(chunker.learned_state["code"], "max_tokens", 100_000)
    monkeypatch.setitem(chunker.learned_state["document"], "max_tokens", 100_000)

    chunks = chunker.chunk_file(SAMPLE_CODE)
    chunks += chunker.chunk_file(SAMPLE_DOCUMENT)

    assert chunks
    assert chunker.code_chunker.max_tokens == 128
    assert chunker.document_chunker.max_tokens == 128
    assert all(simple_token_counter(chunk.content) <= 128 for chunk in chunks)


# --- Error Handling Tests ---


def test_missing_file_raises_file_processing_error(chunker):
    """Test that chunking a missing file path raises FileProcessingError."""
    with pytest.raises(FileProcessingError):
        chunker.chunk_file("/path/to/nonexistent/file.py")


def test_binary_file_raises_unsupported_type(chunker, tmp_path):
    """Test that an unsupported binary file raises UnsupportedFileTypeError."""
    binary_file = tmp_path / "data.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\xff")

    with pytest.raises(UnsupportedFileTypeError):
        chunker.chunk_file(binary_file)


# --- Batch Tests ---


def test_empty_batch_yields_no_chunks(chunker):
    """Test that empty text and file batches yield no chunks."""
    assert list(chunker.chunk_texts([])) == []
    assert list(chunker.chunk_files([])) == []


def test_chunk_texts_routes_each_text_to_its_profile(chunker):
    """Test that chunk_texts classifies each raw string independently."""
    chunks = list(
        chunker.chunk_texts(
            [Path(SAMPLE_CODE).read_text(), Path(SAMPLE_DOCUMENT).read_text()]
        )
    )

    types = {chunk.metadata.inferred_type for chunk in chunks}
    assert types == {"code", "document"}


def test_all_chunks_carry_inferred_type(chunker):
    """Test that every produced chunk is tagged with inferred_type."""
    chunks = list(chunker.chunk_files(SOURCES))

    assert chunks
    for chunk in chunks:
        assert chunk.metadata.inferred_type in {"code", "document"}


def test_separator_is_yielded_between_chunks_per_source(chunker):
    """Test that a separator is yielded between chunks of the same source."""
    separator = object()
    results = list(
        chunker.chunk_files(SOURCES, separator=separator, show_progress=True)
    )

    chunk_count = sum(1 for r in results if r is not separator)
    separator_count = sum(1 for r in results if r is separator)

    assert chunk_count > 1
    assert separator_count == 2


# --- Interface Tests ---


def test_methods_return_the_annotated_type(chunker):
    """Test that each method returns the type its signature promises."""
    assert isinstance(chunker.chunk_text("Hello world."), list)
    assert isinstance(chunker.chunk_file(SAMPLE_CODE), list)
    assert isinstance(chunker.chunk_texts(["Hello world."]), Generator)
    assert isinstance(chunker.chunk_files([SAMPLE_CODE]), Generator)


def test_base_metadata_is_attached_to_every_chunk(chunker):
    """Test that base_metadata reaches every chunk of both profiles."""
    code_chunks = chunker.chunk_text(
        Path(SAMPLE_CODE).read_text(), base_metadata={"page": 3}
    )
    doc_chunks = chunker.chunk_text(
        Path(SAMPLE_DOCUMENT).read_text(), base_metadata={"page": 3}
    )

    assert code_chunks and doc_chunks
    assert all(chunk.metadata.page == 3 for chunk in code_chunks + doc_chunks)
