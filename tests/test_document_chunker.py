import pytest
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from chunklet.exceptions import (
    UnsupportedFileTypeError,
    CallbackExecutionError,
)
from chunklet.document_chunker import DocumentChunker
from chunklet.document_chunker.registry import(
    CustomProcessorRegistry,
    registered_processor,
)
from loguru import logger

# Silent logging
logger.remove()


# --- Fixtures ---

@pytest.fixture
def chunker():
    """
    Provides a DocumentChunker instance initialized with a mocked PlainTextChunker.
    """
    return DocumentChunker()

@pytest.fixture
def registry():
    """Provides a CustomSplitterRegistry instance"""
    return CustomProcessorRegistry()


# --- Core Tests ---

def test_chunk_pdf(chunker):
    """Test chunking a PDF file and its metadata."""
    path = "samples/sample-pdf-a4-size.pdf"
    first_chunk = next(chunker.chunk_pdfs([path]))

    # Check metadata of the first chunk
    first_chunk_metadata = first_chunk.metadata

    assert "source" in first_chunk_metadata
    assert first_chunk_metadata["source"] == path
    assert "page_num" in first_chunk_metadata
    assert "chunk_num" in first_chunk_metadata
    assert "author" in first_chunk_metadata
    assert "title" in first_chunk_metadata
    assert "page_count" in first_chunk_metadata

    
@pytest.mark.parametrize(
    "path",
    [
        "samples/Lorem Ipsum.docx",
        "samples/What_is_rst.rst",
        "samples/complex-layout.rtf",
        "samples/minimal.epub",
    ],
)
def test_chunk_supported_files(chunker, path):
    """Test the main chunk method with various supported file types."""
    chunks = chunker.chunk(path)
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


def test_batch_chunk_with_different_file_type(
    chunker
):
    """Test successful batch chunking of multiple supported file types."""
    paths = ["samples/Lorem Ipsum.docx", "samples/What_is_rst.rst"]
    all_document_chunks = list(chunker.batch_chunk(paths))

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
        assert len(chunks_by_source[path]) > 0


# --- Custom Processor Tests ---

def test_chunk_method_with_custom_processor(tmp_path, mocker, chunker, registry):
    """Test that the chunk method correctly uses a custom processor."""
    # Define and register a mock custom processor callback
    @registered_processor(".mock", name="MockProcessor")
    def mock_custom_processor_callback(file_path: str) -> str:
        return "Processed failed."

    try:
        # Create a dummy file with the custom extension
        dummy_file = tmp_path / "test.mock"
        dummy_file.write_text(
            "Original content that should be ignored by custom processor."
        )

        # Chunk the dummy file
        chunks = chunker.chunk(dummy_file)

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
            lambda file_path: [
                "This is a list.",
                "Not a string.",
            ],  # Returns list, not str
            r"Input should be a valid string",
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

    @registered_processor(".txt", name=processor_name)
    def temp_processor(file_path: str):
        return callback_func(file_path)

    try:
        with pytest.raises(CallbackExecutionError, match=re.escape(expected_match)):
            chunker.chunk(dummy_file)
    finally:
        # Unregister to not affect other tests
        registry.unregister(".txt")
