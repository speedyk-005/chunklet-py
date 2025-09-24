import pytest
import re
from pathlib import Path
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
from chunklet import (
    PlainTextChunker,
    DocumentChunker,
    InvalidInputError,
    UnsupportedFileTypeError,
    FileProcessingError,
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
            InvalidInputError,  
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
    chunks = list(document_chunker.chunk_pdfs([path])) 

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
def test_chunk_files(document_chunker, mock_plain_text_chunker, path):
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
        match=re.escape("File type '.xyz' is not supported.")
    ):
        document_chunker.chunk(unsupported_file)


def test_batch_chunk_with_different_file_type(document_chunker, mock_plain_text_chunker):
    """Test successful batch chunking of multiple supported file types."""
    mock_plain_text_chunker.verbose = True
    paths = ["samples/sample-pdf-a4-size.pdf", "samples/Lorem.docx"]
    all_document_chunks = list(document_chunker.batch_chunk(paths))

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
    

def test_chunk_method_with_custom_processor(
    document_chunker, mock_plain_text_chunker, tmp_path
):
    """Test that the chunk method correctly uses a custom processor."""

    # Define a mock custom processor callback
    def mock_custom_processor_callback(file_path: str) -> str:
        return f"Processed failed."

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
    expected_content_prefix = f"Processed failed."
    assert len(chunks) > 0
    assert chunks[0].content.startswith(expected_content_prefix)
    assert "source" in chunks[0].metadata
    assert chunks[0].metadata["source"] == str(dummy_file)


@pytest.mark.parametrize(
    "processor_name, callback_func, expected_match",
    [
        (
            "InvalidReturnProcessor",
            lambda file_path: ["This is a list.", "Not a string."],  # Returns list, not str
            "Custom processor 'InvalidReturnProcessor' callback returned an invalid type.",
        ),
        (
            "FailingProcessor",
            lambda file_path: (_ for _ in ()).throw(ValueError("Intentional failure in custom processor.")),
            "Custom processor 'FailingProcessor' failed",
        ),
    ],
)
def test_custom_processor_validation_scenarios(
    document_chunker, mock_plain_text_chunker, tmp_path, processor_name, callback_func, expected_match
):
    """Test various custom processor validation scenarios."""
    # Create a dummy file
    dummy_file = tmp_path / "dummy_file.txt"
    dummy_file.write_text("Some content.")

    custom_processors = [
        {
            "name": processor_name,
            "file_extensions": ".txt",
            "callback": callback_func,
        }
    ]

    # Re-initialize DocumentChunker with the custom processor
    document_chunker = DocumentChunker(
        mock_plain_text_chunker, custom_processors=custom_processors
    )

    with pytest.raises(FileProcessingError, match=re.escape(expected_match)):
        document_chunker.chunk(dummy_file)
