import re
import pytest
from collections import defaultdict
from chunklet.document_chunker import DocumentChunker, CustomProcessorRegistry
from chunklet import (
    UnsupportedFileTypeError,
    CallbackError,
)


# --- Fixtures ---


@pytest.fixture
def chunker():
    """Provides a DocumentChunker instance."""
    return DocumentChunker()


@pytest.fixture
def registry():
    """Provides a CustomSplitterRegistry instance"""
    return CustomProcessorRegistry()


# --- Core Tests ---


@pytest.mark.parametrize(
    "path",
    [
        "samples/What_is_rst.rst",
        "samples/complex-layout.rtf",
        "samples/example.xlsx",
        "samples/username.csv",
    ],
)
def test_chunk_simple_files(chunker, path):
    """Test the main chunk method with various supported file types."""
    chunks = chunker.chunk(path, max_sentences=5)
    assert len(chunks) > 0
    assert "source" in chunks[0].metadata


def test_chunk_unsupported_file(chunker, tmp_path):
    """Test that chunking raises an error for unsupported file types."""
    # Test with a file type that is not in GENERAL_TEXT_EXTENSIONS
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test")
    with pytest.raises(
        UnsupportedFileTypeError, match=re.escape("File type '.xyz' is not supported.")
    ):
        chunker.chunk(unsupported_file)


def test_batch_chunk_with_different_file_type(chunker):
    """Test successful batch chunking of multiple supported file types."""
    paths = [
        "samples/Lorem Ipsum.docx",
        "samples/What_is_rst.rst",
        "samples/minimal.epub",
        "samples/sample-pdf-a4-size.pdf",
        "samples/file-sample_100kB.odt",
    ]
    all_document_chunks = list(chunker.batch_chunk(paths, max_sentences=5))

    # Check that we got some chunks
    assert len(all_document_chunks) > 0

    # Group chunks by source file
    chunks_by_source = defaultdict(list)
    for chunk in all_document_chunks:
        chunks_by_source[chunk.metadata.source].append(chunk)

    # Check that we have chunks from all input files
    assert len(chunks_by_source) == len(paths)
    for path in paths:
        assert path in chunks_by_source
        assert chunks_by_source[path][0].metadata  # assert metadata presence
        assert len(chunks_by_source[path]) > 0


def test_chunk_method_unsupported_iterable_processor(chunker):
    """Test that chunk method raises UnsupportedFileTypeError when processor returns iterable."""
    # PDF files return an iterable, so using chunk() method should fail with specific error
    with pytest.raises(
        UnsupportedFileTypeError,
        match=re.escape(
            "File type '.pdf' is not supported by the general chunk method.\n"
            "Reason: The processor for this file returns iterable, "
            "so it must be processed in parallel for efficiency.\n"
            "💡 Hint: use `chunker.batch_chunk([file.ext])` for this file type."
        ),
    ):
        chunker.chunk("samples/sample-pdf-a4-size.pdf", max_sentences=5)


# --- Custom Processor Tests ---


def test_chunk_method_with_custom_processor(tmp_path, mocker, chunker, registry):
    """Test that the chunk method correctly uses a custom processor."""

    # Define and register a mock custom processor callback
    @registry.register(".mock", name="MockProcessor")
    def mock_custom_processor_callback(file_path: str) -> tuple[str, dict]:
        return "Processed failed.", {"mock": "metadata"}

    try:
        # Create a dummy file with the custom extension
        dummy_file = tmp_path / "test.mock"
        dummy_file.write_text(
            "Original content that should be ignored by custom processor."
        )

        # Chunk the dummy file
        chunks = chunker.chunk(dummy_file, max_sentences=5)

        # Assert that the custom processor's output was used
        expected_content_prefix = "Processed failed."
        assert len(chunks) > 0
        assert chunks[0].content.startswith(expected_content_prefix)
        assert "source" in chunks[0].metadata
        assert chunks[0].metadata["source"] == str(dummy_file)
    finally:
        # Unregister the custom processor after the test
        registry.unregister(".mock")


@pytest.mark.parametrize(
    "processor_name, callback_func, expected_match",
    [
        (
            "InvalidReturnProcessor",
            lambda file_path: 12345,  # Returns an int, not tuple(str|iterable, dict)
            r"Make sure your processor returns a tuple of (text/texts, metadata_dict).",
        ),
        (
            "FailingProcessor",
            lambda file_path: (_ for _ in ()).throw(
                ValueError("Intentional failure in custom processor.")
            ),
            "Processor 'FailingProcessor' for extension '.txt' raised an exception",
        ),
    ],
)
def test_custom_processor_validation_scenarios(
    tmp_path,
    processor_name,
    callback_func,
    expected_match,
    mocker,
    chunker,
    registry,
):
    """Test various custom processor validation scenarios."""
    # Create a dummy file
    dummy_file = tmp_path / "dummy_file.txt"
    dummy_file.write_text("Some content.")

    @registry.register(".txt", name=processor_name)
    def temp_processor(file_path: str):
        return callback_func(file_path), {"mock": "metadata"}

    try:
        with pytest.raises(CallbackError, match=re.escape(expected_match)):
            chunker.chunk(dummy_file, max_sentences=5)
    finally:
        # Unregister to not affect other tests
        registry.unregister(".txt")


def test_batch_chunk_custom_processor_error_handling(chunker, registry, tmp_path):
    """Test batch_chunk error handling with failing custom processor."""
    # Create test files with different extensions
    file1 = tmp_path / "test1.txt"  # Will use failing processor
    file1.write_text("content1")
    file2 = tmp_path / "test2.md"  # Will use default processor (should work)
    file2.write_text("content2")

    @registry.register(".txt", name="FailingBatchProcessor")
    def failing_processor(file_path: str):
        raise ValueError("Custom processor failed in batch")

    try:
        # Test on_errors="raise" - should re-raise
        with pytest.raises(CallbackError):
            list(
                chunker.batch_chunk([file1, file2], max_sentences=5, on_errors="raise")
            )

        # Test on_errors="skip" - should skip failed file, process .md file
        chunks = list(
            chunker.batch_chunk([file1, file2], max_sentences=5, on_errors="skip")
        )
        assert len(chunks) >= 1  # Should get chunks from successful .md file

        # Test on_errors="break" - should stop on first error (txt file)
        chunks = list(
            chunker.batch_chunk([file1, file2], max_sentences=5, on_errors="break")
        )
        assert len(chunks) == 0  # Should get no chunks since txt fails first

    finally:
        registry.unregister(".txt")
