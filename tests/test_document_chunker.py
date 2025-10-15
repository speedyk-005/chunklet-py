import pytest
import re
from concurrent.futures import ThreadPoolExecutor
from chunklet.exceptions import (
    UnsupportedFileTypeError,
    CallbackExecutionError,
)
from chunklet.document_chunker import (
    DocumentChunker,
    registered_processor,
    unregister_processor,
)
from chunklet.plain_text_chunker import PlainTextChunker
from loguru import logger

# Silent logging
logger.remove()


# --- Fixtures ---
@pytest.fixture
def mock_plain_text_chunker(mocker):
    """Mock PlainTextChunker to isolate DocumentChunker logic"""
    mock = mocker.create_autospec(PlainTextChunker, instance=True)
    mock.verbose = False

    def mock_chunk_impl(text, **kwargs):
        lines = text.splitlines()
        chunks = []
        for i in range(0, len(lines), 2):
            chunk_content = "\n".join(lines[i : i + 2])
            chunks.append(chunk_content)
        return chunks

    def mock_batch_chunk_impl(texts, **kwargs):
        chunk_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key
            in [
                "lang",
                "mode",
                "max_tokens",
                "max_sentences",
                "overlap_percent",
                "offset",
                "token_counter",
            ]
        }
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(mock.chunk, text, **chunk_kwargs) for text in texts
            ]
            return [future.result() for future in futures]

    mock.chunk.side_effect = mock_chunk_impl
    mock.batch_chunk.side_effect = mock_batch_chunk_impl
    return mock


@pytest.fixture
def document_chunker(mock_plain_text_chunker):
    """
    Provides a DocumentChunker instance initialized with a mocked PlainTextChunker.
    """
    return DocumentChunker(verbose=False, plain_text_chunker=mock_plain_text_chunker)


# --- Core Tests ---


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


def test_chunk_unsupported_file_type(document_chunker, tmp_path):
    """Test that chunking raises an error for unsupported file types."""
    # Test with a file type that is not in GENERAL_TEXT_EXTENSIONS
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test")
    with pytest.raises(
        UnsupportedFileTypeError, match=re.escape("File type '.xyz' is not supported.")
    ):
        document_chunker.chunk(unsupported_file)


def test_batch_chunk_with_different_file_type(
    document_chunker, mock_plain_text_chunker
):
    """Test successful batch chunking of multiple supported file types."""
    from collections import defaultdict

    mock_plain_text_chunker.verbose = True
    paths = ["samples/Lorem.docx", "samples/What_is_rst.rst"]
    all_document_chunks = list(document_chunker.batch_chunk(paths))

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
def test_chunk_method_with_custom_processor(mock_plain_text_chunker, tmp_path, mocker):
    """Test that the chunk method correctly uses a custom processor."""

    # Patch PlainTextChunker within DocumentChunker module
    mocker.patch(
        "chunklet.document_chunker.document_chunker.PlainTextChunker",
        return_value=mock_plain_text_chunker,
    )

    # Define and register a mock custom processor callback
    @registered_processor(".mock", name="MockProcessor")
    def mock_custom_processor_callback(file_path: str) -> str:
        return "Processed failed."

    try:
        # Initialize DocumentChunker (without custom_processors arg)
        document_chunker = DocumentChunker()

        # Create a dummy file with the custom extension
        dummy_file = tmp_path / "test.mock"
        dummy_file.write_text(
            "Original content that should be ignored by custom processor."
        )

        # Chunk the dummy file
        chunks = document_chunker.chunk(dummy_file)

        # Assert that the custom processor's output was used
        expected_content_prefix = "Processed failed."
        assert len(chunks) > 0
        assert chunks[0].content.startswith(expected_content_prefix)
        assert "source" in chunks[0].metadata
        assert chunks[0].metadata["source"] == str(dummy_file)
    finally:
        # Unregister the custom processor after the test
        unregister_processor(".mock")


@pytest.mark.parametrize(
    "processor_name, callback_func, expected_match",
    [
        (
            "InvalidReturnProcessor",
            lambda file_path: [
                "This is a list.",
                "Not a string.",
            ],  # Returns list, not str
            "Document processor 'InvalidReturnProcessor' for extension '.txt' returned an invalid type",
        ),
        (
            "FailingProcessor",
            lambda file_path: (_ for _ in ()).throw(
                ValueError("Intentional failure in custom processor.")
            ),
            "Document processor 'FailingProcessor' for extension '.txt' raised an exception",
        ),
    ],
)
def test_custom_processor_validation_scenarios(
    mock_plain_text_chunker,
    tmp_path,
    processor_name,
    callback_func,
    expected_match,
    mocker,
):
    """Test various custom processor validation scenarios."""
    # Patch PlainTextChunker within DocumentChunker module
    mocker.patch(
        "chunklet.document_chunker.document_chunker.PlainTextChunker",
        return_value=mock_plain_text_chunker,
    )

    # Create a dummy file
    dummy_file = tmp_path / "dummy_file.txt"
    dummy_file.write_text("Some content.")

    @registered_processor(".txt", name=processor_name)
    def temp_processor(file_path: str):
        return callback_func(file_path)

    try:
        document_chunker = DocumentChunker()
        with pytest.raises(CallbackExecutionError, match=re.escape(expected_match)):
            document_chunker.chunk(dummy_file)
    finally:
        # Unregister to not affect other tests
        unregister_processor(".txt")
