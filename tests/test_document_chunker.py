import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
from chunklet import (
    PlainTextChunker,
    DocumentChunker,
    InvalidInputError,
    UnsupportedFileTypeError,
)

from loguru import logger

# Silent logging
logger.remove()

@pytest.fixture
def mock_plain_text_chunker():
    """Mock PlainTextChunker to isolate DocumentChunker logic"""
    mock = MagicMock(spec=PlainTextChunker)
    mock.verbose = False

    def mock_chunk_impl(text, **kwargs):
        lines = text.splitlines()
        chunks = []
        for i in range(0, len(lines), 2):
            chunk_content = "\n".join(lines[i : i + 2])
            chunks.append(chunk_content)
        return chunks

    def mock_batch_chunk_impl(texts, **kwargs):
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(mock.chunk, text, **kwargs) for text in texts]
            return [future.result() for future in futures]

    mock.chunk.side_effect = mock_chunk_impl
    mock.batch_chunk.side_effect = mock_batch_chunk_impl
    return mock


@pytest.fixture
def document_chunker(mock_plain_text_chunker):
    return DocumentChunker(mock_plain_text_chunker)


# Test DocumentChunker Initialization
@pytest.mark.parametrize(
    "input, expected_exception, match_string",
    [
        (MagicMock(spec=PlainTextChunker), None, ""),
        (
            "not a PlainTextChunker instance",
            TypeError,
            "plain_text_chunker must be an instance of PlainTextChunker",
        ),
    ],
)
def test_document_chunker_init(input, expected_exception, match_string):
    """Test DocumentChunker initialization with valid and invalid PlainTextChunker instances."""
    if expected_exception:
        with pytest.raises(expected_exception, match=match_string):
            DocumentChunker(input)
    else:
        chunker = DocumentChunker(input)
        assert isinstance(chunker.plain_text_chunker, PlainTextChunker)


def test_chunk_pdf(document_chunker, mock_plain_text_chunker):
    """Test chunking a PDF file and its metadata."""
    mock_plain_text_chunker.verbose = True
    path = "samples/sample-pdf-a4-size.pdf"
    chunks = document_chunker.chunk(path)

    assert len(chunks) > 0

    # Check metadata of the first chunk
    first_chunk_metadata = chunks[0].metadata

    assert "source" in first_chunk_metadata
    assert isinstance(first_chunk_metadata["source"], str)
    assert first_chunk_metadata["source"] == path

    assert "page_num" in first_chunk_metadata
    assert isinstance(first_chunk_metadata["page_num"], int)

    assert "chunk_num" in first_chunk_metadata
    assert isinstance(first_chunk_metadata["chunk_num"], int)

    assert "author" in first_chunk_metadata
    assert isinstance(first_chunk_metadata["author"], (str, type(None)))

    assert "title" in first_chunk_metadata
    assert isinstance(first_chunk_metadata["title"], (str, type(None)))

    assert "page_count" in first_chunk_metadata
    assert isinstance(first_chunk_metadata["page_count"], int)

    mock_plain_text_chunker.batch_chunk.assert_called_once()
    mock_plain_text_chunker.chunk.assert_called()


# Test chunk method for different file types
@pytest.mark.parametrize(
    "path",
    [
        "samples/Lorem.docx",
        "samples/What_is_rst.rst",
        "samples/complex-layout.rtf",
    ],
)
def test_chunk_files(
    document_chunker, mock_plain_text_chunker, path
):
    """Test the main chunk method with various supported file types."""
    mock_plain_text_chunker.reset_mock()
    mock_plain_text_chunker.verbose = True
    chunks = document_chunker.chunk(path)
    assert len(chunks) > 0
    assert "source" in chunks[0].metadata
    mock_plain_text_chunker.chunk.assert_called_once()
    mock_plain_text_chunker.batch_chunk.assert_not_called()


def test_chunk_unsupported_file_type(document_chunker, tmp_path):
    """Test that chunking raises an error for unsupported file types."""
    # Test with a file type that is not in GENERAL_TEXT_EXTENSIONS
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test")
    with pytest.raises(
        UnsupportedFileTypeError,
        match="File type '.xyz' is not supported for general document chunking.",
    ):
        document_chunker.chunk(unsupported_file)


# Test bulk_chunk method with multiple files
def test_bulk_chunk_happy_path(document_chunker, mock_plain_text_chunker):
    """Test successful bulk chunking of multiple supported file types."""
    mock_plain_text_chunker.verbose = True
    paths = ["samples/sample-pdf-a4-size.pdf", "samples/Lorem.docx"]
    all_document_chunks = document_chunker.bulk_chunk(paths)

    assert len(all_document_chunks) == len(paths)
    mock_plain_text_chunker.batch_chunk.assert_called_once()
    mock_plain_text_chunker.chunk.assert_called()

    all_chunks_flat = [
        chunk for doc_chunks in all_document_chunks for chunk in doc_chunks
    ]
    pdf_chunks = [
        chunk
        for chunk in all_chunks_flat
        if "sample-pdf-a4-size.pdf" in chunk.metadata["source"]
    ]
    docx_chunks = [
        chunk for chunk in all_chunks_flat if "Lorem.docx" in chunk.metadata["source"]
    ]
    assert len(pdf_chunks) > 0
    assert len(docx_chunks) > 0


def test_bulk_chunk_with_non_existent_file(document_chunker, mock_plain_text_chunker):
    """Test that bulk_chunk skips non-existent files."""
    paths = ["samples/Lorem.docx", "non_existent_file.txt"]
    result = document_chunker.bulk_chunk(paths)
    assert len(result) == 1
    assert "Lorem.docx" in result[0][0].metadata["source"]
    mock_plain_text_chunker.batch_chunk.assert_called_once()


def test_bulk_chunk_with_unsupported_file(
    document_chunker, mock_plain_text_chunker, tmp_path
):
    """Test that bulk_chunk skips unsupported file types."""
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test")
    paths = ["samples/Lorem.docx", str(unsupported_file)]
    result = document_chunker.bulk_chunk(paths)
    assert len(result) == 1
    assert "Lorem.docx" in result[0][0].metadata["source"]
    mock_plain_text_chunker.batch_chunk.assert_called_once()


def test_bulk_chunk_with_empty_list(document_chunker, mock_plain_text_chunker):
    """Test that bulk_chunk handles an empty list of paths."""
    assert document_chunker.bulk_chunk([]) == []
    mock_plain_text_chunker.batch_chunk.assert_not_called()


def test_bulk_chunk_with_only_invalid_paths(
    document_chunker, mock_plain_text_chunker, tmp_path
):
    """Test that bulk_chunk handles a list of all-invalid paths."""
    unsupported_file = tmp_path / "unsupported.xyz"
    unsupported_file.write_text("test")
    paths = ["non_existent_file.txt", str(unsupported_file)]
    result = document_chunker.bulk_chunk(paths)
    assert result == []
    mock_plain_text_chunker.batch_chunk.assert_not_called()


def test_chunk_method_with_custom_processor(
    document_chunker, mock_plain_text_chunker, tmp_path
):
    """Test that the chunk method correctly uses a custom processor."""

    # Define a mock custom processor callback
    def mock_custom_processor_callback(file_path: str) -> str:
        return f"Custom processed content from {file_path}. Line 1. Line 2. Line 3."

    # Create a custom processor
    custom_processor = [
        {
            "name": "MockProcessor",
            "file_extensions": ".mock",
            "callback": mock_custom_processor_callback,
        }
    ]

    # Re-initialize DocumentChunker with the custom processor
    document_chunker = DocumentChunker(
        mock_plain_text_chunker, custom_processors=custom_processor
    )

    # Create a dummy file with the custom extension
    dummy_file = tmp_path / "test.mock"
    dummy_file.write_text(
        "Original content that should be ignored by custom processor."
    )

    # Chunk the dummy file
    chunks = document_chunker.chunk(dummy_file)

    # Assert that the custom processor's output was used
    expected_content_prefix = f"Custom processed content from {dummy_file}"
    assert len(chunks) > 0
    assert chunks[0].content.startswith(expected_content_prefix)
    assert "source" in chunks[0].metadata
    assert chunks[0].metadata["source"] == str(dummy_file)

    # Verify that plain_text_chunker.chunk was called with the custom processed text
    mock_plain_text_chunker.chunk.assert_called_once_with(
        text=f"Custom processed content from {dummy_file}. Line 1. Line 2. Line 3.",
        lang="auto",
        mode="sentence",
        max_tokens=256,
        max_sentences=12,
        overlap_percent=20,
        offset=0,
        token_counter=None,
    )
